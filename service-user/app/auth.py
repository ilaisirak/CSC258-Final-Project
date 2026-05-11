# Authorization for the user service.
#
# Authentication lives in service-auth. service-user does the same
# thing every other backend does: trust the gateway-injected
# X-Auth-User-* headers carried over mTLS. Mirror of service-class/auth.py.

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
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


async def get_current_user(
    x_auth_user_id:    Optional[str] = Header(default=None),
    x_auth_user_role:  Optional[str] = Header(default=None),
    x_auth_user_name:  Optional[str] = Header(default=None),
    x_auth_user_email: Optional[str] = Header(default=None),
) -> CurrentUser:
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