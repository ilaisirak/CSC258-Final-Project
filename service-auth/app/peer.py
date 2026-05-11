# mTLS client helper for outbound calls to peer services.
#
# service-auth talks to service-user over mTLS to fetch user records by
# email/id and to create new users on registration. Cluster-internal
# only — never exposed publicly.

import os
import ssl

import httpx

SERVICE_NAME = os.getenv("SERVICE_NAME", "")
CERTS_DIR = os.getenv("CERTS_DIR", "/etc/svc-certs")

_CA_FILE = os.path.join(CERTS_DIR, "ca.crt")
_CERT_FILE = os.path.join(CERTS_DIR, f"{SERVICE_NAME}.crt") if SERVICE_NAME else None
_KEY_FILE = os.path.join(CERTS_DIR, f"{SERVICE_NAME}.key") if SERVICE_NAME else None

USER_SERVICE_URL = "https://service-user:8000"


def _build_ssl_context() -> ssl.SSLContext:
    """Build an SSLContext trusting our dev CA and presenting our client cert.

    httpx 0.28 deprecated passing both ``verify=<ca>`` and ``cert=(crt, key)``
    to AsyncClient; the combination no longer reliably loads the client cert,
    causing the server to drop the TLS handshake. We build an explicit
    SSLContext instead and pass it via ``verify=``.
    """
    if not _CERT_FILE or not _KEY_FILE:
        raise RuntimeError(
            "SERVICE_NAME env var is required to build an mTLS client"
        )
    ctx = ssl.create_default_context(cafile=_CA_FILE)
    ctx.load_cert_chain(certfile=_CERT_FILE, keyfile=_KEY_FILE)
    return ctx


def mtls_client(**kwargs) -> httpx.AsyncClient:
    """Return an httpx.AsyncClient configured for cluster-internal mTLS."""
    kwargs.setdefault("timeout", 5.0)
    return httpx.AsyncClient(verify=_build_ssl_context(), **kwargs)
