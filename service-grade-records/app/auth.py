# Authorization client for this service.
#
# Authentication happens at the API gateway: nginx runs `auth_request`
# against service-user/auth/verify on every protected /api/* request.
# On success the gateway captures the verified identity into these
# request headers and forwards them to the upstream:
#
#     X-Auth-User-Id     uuid
#     X-Auth-User-Role   "student" | "professor"
#     X-Auth-User-Name   string
#     X-Auth-User-Email  string
#
# Cluster-internal traffic is mTLS, so the only callers that can reach
# this service are (a) the gateway, presenting frontend.crt, and (b)
# peer backends, presenting their own service certs. Both are trusted
# to have already authenticated the end user upstream — there is no
# end-user JWT to validate here, only the identity headers to read.

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel


class CurrentUser(BaseModel):
    """Subset of the verified identity used for authorization decisions."""
    id: str
    role: str
    name: Optional[str] = None
    email: Optional[str] = None


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
    )


async def get_current_user(
    x_auth_user_id:    Optional[str] = Header(default=None),
    x_auth_user_role:  Optional[str] = Header(default=None),
    x_auth_user_name:  Optional[str] = Header(default=None),
    x_auth_user_email: Optional[str] = Header(default=None),
) -> CurrentUser:
    """Resolve the calling user from the gateway-injected identity headers."""
    if not x_auth_user_id or not x_auth_user_role:
        raise _unauthorized("Missing identity headers")
    return CurrentUser(
        id=x_auth_user_id,
        role=x_auth_user_role,
        name=x_auth_user_name,
        email=x_auth_user_email,
    )


def require_role(*roles: str):
    """Dependency factory enforcing that the caller has one of the given roles."""
    async def dep(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role in {list(roles)}",
            )
        return user
    return dep


async def get_auth_header(
    x_auth_user_id:    Optional[str] = Header(default=None),
    x_auth_user_role:  Optional[str] = Header(default=None),
    x_auth_user_name:  Optional[str] = Header(default=None),
    x_auth_user_email: Optional[str] = Header(default=None),
) -> dict:
    """Build identity headers to forward on outbound peer-service calls.

    Peer services trust X-Auth-User-* exactly because the underlying
    transport is mTLS — only certs signed by our CA can deliver these
    headers, so a service-to-service call from another backend is just
    as trusted as a call from the gateway.
    """
    headers: dict = {}
    if x_auth_user_id:
        headers["X-Auth-User-Id"] = x_auth_user_id
    if x_auth_user_role:
        headers["X-Auth-User-Role"] = x_auth_user_role
    if x_auth_user_name:
        headers["X-Auth-User-Name"] = x_auth_user_name
    if x_auth_user_email:
        headers["X-Auth-User-Email"] = x_auth_user_email
    return headers
