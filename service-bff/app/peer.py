# mTLS client helper for outbound peer-to-peer calls.
#
# All inter-service traffic in this project goes over HTTPS with mutual
# TLS: the receiving service requires a client certificate signed by
# our development CA (see scripts/gen-certs.ps1). This module builds an
# httpx.AsyncClient pre-configured with this service's own client cert
# and the trust anchor, so callers just write:
#
#     async with mtls_client() as client:
#         await client.get(f"{USER_SERVICE_URL}/users/by-id/{uid}")
#
# Service URLs are exported here too so individual route modules don't
# repeat the https://service-name:8000 string.

import os
import ssl

import httpx

SERVICE_NAME = os.getenv("SERVICE_NAME", "")
CERTS_DIR = os.getenv("CERTS_DIR", "/etc/svc-certs")

_CA_FILE = os.path.join(CERTS_DIR, "ca.crt")
_CERT_FILE = os.path.join(CERTS_DIR, f"{SERVICE_NAME}.crt") if SERVICE_NAME else None
_KEY_FILE = os.path.join(CERTS_DIR, f"{SERVICE_NAME}.key") if SERVICE_NAME else None

# Cluster-internal URLs for the other backends. Each one is the DNS name
# from docker-compose / k8s with port 8000 (uvicorn) over HTTPS.
USER_SERVICE_URL       = "https://service-user:8000"
CLASS_SERVICE_URL      = "https://service-class:8000"
ASSIGNMENT_SERVICE_URL = "https://service-assignment:8000"
SUBMISSION_SERVICE_URL = "https://service-submission:8000"
GRADING_SERVICE_URL    = "https://service-grade-records:8000"
ENROLLMENT_SERVICE_URL = "https://service-enrollment:8000"


def _build_ssl_context() -> ssl.SSLContext:
    """Build an SSLContext trusting our dev CA and presenting our client cert.

    httpx 0.28 deprecated combining ``verify=<ca>`` with ``cert=(crt, key)``;
    in practice the client certificate is no longer presented during the
    TLS handshake, so the peer drops the connection. We construct an
    explicit SSLContext and pass it via ``verify=`` instead.
    """
    if not _CERT_FILE or not _KEY_FILE:
        raise RuntimeError(
            "SERVICE_NAME env var is required to build an mTLS client"
        )
    ctx = ssl.create_default_context(cafile=_CA_FILE)
    ctx.load_cert_chain(certfile=_CERT_FILE, keyfile=_KEY_FILE)
    return ctx


def mtls_client(**kwargs) -> httpx.AsyncClient:
    """Return an httpx.AsyncClient configured for cluster-internal mTLS.

    Extra keyword arguments are forwarded to httpx.AsyncClient (e.g.
    `timeout=5.0`).
    """
    return httpx.AsyncClient(verify=_build_ssl_context(), **kwargs)
