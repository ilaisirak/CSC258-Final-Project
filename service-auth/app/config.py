import os

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# service-auth owns ONLY the refresh_tokens table. The users table lives in
# service-user and is reached over mTLS HTTP, never via a direct DB join.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://dev:devpassword@postgres-auth:5432/auth",
)

# ---------------------------------------------------------------------------
# Auth secrets and lifetimes
# ---------------------------------------------------------------------------
# AUTH_SECRET is the HMAC key used to sign and verify access tokens. ONLY
# this service ever reads it. Peer services trust gateway-injected
# X-Auth-User-* headers (added after the gateway calls /auth/verify) and
# never decode JWTs themselves, so the secret never has to leave this
# service. Override in any non-dev deployment.
AUTH_SECRET = os.getenv("AUTH_SECRET", "change-me-in-production")

# Refuse to boot in non-dev environments if AUTH_SECRET is left at any
# of the well-known development defaults. Imported at startup so the
# failure is loud and immediate rather than a silent insecure run.
ENV = os.getenv("ENV", "dev").lower()
_KNOWN_DEV_SECRETS = {"change-me-in-production", "dev", "devsecret", "secret"}
if ENV != "dev" and AUTH_SECRET in _KNOWN_DEV_SECRETS:
    raise RuntimeError(
        "AUTH_SECRET is set to a known development default in a non-dev "
        "environment. Set AUTH_SECRET to a strong random value."
    )

# Access token lifetime — kept short (15 minutes) so a stolen token expires
# quickly. Long-lived sessions are maintained via refresh tokens.
JWT_LIFETIME_SECONDS = int(os.getenv("JWT_LIFETIME_SECONDS", str(15 * 60)))

# Refresh token lifetime — 7 days. Refresh tokens are opaque random strings
# stored hashed in the database, delivered as an HttpOnly cookie, and
# rotated on every /auth/refresh.
REFRESH_LIFETIME_SECONDS = int(
    os.getenv("REFRESH_LIFETIME_SECONDS", str(7 * 24 * 60 * 60))
)

# Cookie name + path for the refresh token. Path is restricted to
# /api/auth so the browser only sends it on auth endpoints, eliminating
# CSRF risk on data routes.
REFRESH_COOKIE_NAME = os.getenv("REFRESH_COOKIE_NAME", "grading_refresh")
REFRESH_COOKIE_PATH = "/api/auth"

# When true the cookie is marked Secure (HTTPS-only). Defaults to false
# for http://localhost compose; set true in any deployment that
# terminates TLS at the gateway.
REFRESH_COOKIE_SECURE = os.getenv("REFRESH_COOKIE_SECURE", "false").lower() == "true"
