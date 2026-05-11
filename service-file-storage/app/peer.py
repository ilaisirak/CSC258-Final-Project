import os
import ssl

import httpx

SERVICE_NAME = os.getenv("SERVICE_NAME", "")
CERTS_DIR = os.getenv("CERTS_DIR", "/etc/svc-certs")

_CA_FILE = os.path.join(CERTS_DIR, "ca.crt")
_CERT_FILE = os.path.join(CERTS_DIR, f"{SERVICE_NAME}.crt") if SERVICE_NAME else None
_KEY_FILE = os.path.join(CERTS_DIR, f"{SERVICE_NAME}.key") if SERVICE_NAME else None


def _build_ssl_context() -> ssl.SSLContext:
    """Build an SSLContext trusting the dev CA and presenting our client cert.

    httpx 0.28 deprecated combining ``verify=<ca>`` with ``cert=(crt, key)``;
    in practice the client certificate is no longer presented during the
    TLS handshake, so the peer drops the connection. Use an explicit
    SSLContext via ``verify=`` instead.
    """
    if not _CERT_FILE or not _KEY_FILE:
        raise RuntimeError(
            "SERVICE_NAME env var is required to build an mTLS client"
        )
    ctx = ssl.create_default_context(cafile=_CA_FILE)
    ctx.load_cert_chain(certfile=_CERT_FILE, keyfile=_KEY_FILE)
    return ctx


def mtls_client(**kwargs) -> httpx.AsyncClient:
    kwargs.setdefault("timeout", 5.0)
    return httpx.AsyncClient(verify=_build_ssl_context(), **kwargs)
