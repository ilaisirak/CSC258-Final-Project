# Authentication wiring for the auth service.
#
# Configures fastapi-users with:
#   - an HTTP-backed user database adapter (HTTPUserDatabase) that proxies
#     reads and writes to service-user instead of touching SQLAlchemy.
#   - a custom JWT strategy that embeds role/name/email claims so peer
#     services receive identity in a single round-trip.
#   - opaque refresh-token issuance / rotation / revocation against
#     service-auth's own database.
#
# Password hashing, registration validation, and timing-safe credential
# comparison are reused from fastapi-users so the security primitives
# stay battle-tested.

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator, Dict, Optional, Tuple

import httpx
from fastapi import Depends, HTTPException, status
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import BaseUserDatabase
from fastapi_users.exceptions import UserAlreadyExists
from fastapi_users.jwt import generate_jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import AUTH_SECRET, JWT_LIFETIME_SECONDS, REFRESH_LIFETIME_SECONDS
from app.database import AsyncSessionLocal
from app.models import RefreshToken
from app.peer import USER_SERVICE_URL, mtls_client
from app.schemas import AuthUser


# ---------------------------------------------------------------------------
# HTTP-backed user database
# ---------------------------------------------------------------------------
# Replaces the standard SQLAlchemyUserDatabase. Every method calls
# service-user over mTLS. service-user owns the users table; service-auth
# never touches it directly. This keeps the bounded contexts clean: this
# service is responsible for credentials and tokens, the user service is
# responsible for profile data.

class HTTPUserDatabase(BaseUserDatabase[AuthUser, uuid.UUID]):

    async def get(self, id: uuid.UUID) -> Optional[AuthUser]:
        async with mtls_client() as client:
            try:
                r = await client.get(
                    f"{USER_SERVICE_URL}/users/internal/by-id/{id}"
                )
            except httpx.RequestError:
                return None
        if r.status_code != 200:
            return None
        return AuthUser(**r.json())

    async def get_by_email(self, email: str) -> Optional[AuthUser]:
        async with mtls_client() as client:
            try:
                r = await client.get(
                    f"{USER_SERVICE_URL}/users/internal/by-email",
                    params={"email": email},
                )
            except httpx.RequestError:
                return None
        if r.status_code != 200:
            return None
        return AuthUser(**r.json())

    async def get_by_oauth_account(
        self, oauth: str, account_id: str
    ) -> Optional[AuthUser]:
        # OAuth is not supported. Returning None means fastapi-users will
        # treat the user as not found.
        return None

    async def create(self, create_dict: Dict[str, Any]) -> AuthUser:
        async with mtls_client() as client:
            r = await client.post(
                f"{USER_SERVICE_URL}/users/internal",
                json=_jsonable(create_dict),
            )
        if r.status_code == 409:
            raise UserAlreadyExists()
        if r.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"User service error: {r.status_code} {r.text}",
            )
        return AuthUser(**r.json())

    async def update(
        self, user: AuthUser, update_dict: Dict[str, Any]
    ) -> AuthUser:
        async with mtls_client() as client:
            r = await client.patch(
                f"{USER_SERVICE_URL}/users/internal/by-id/{user.id}",
                json=_jsonable(update_dict),
            )
        if r.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"User service error: {r.status_code} {r.text}",
            )
        return AuthUser(**r.json())

    async def delete(self, user: AuthUser) -> None:
        async with mtls_client() as client:
            r = await client.delete(
                f"{USER_SERVICE_URL}/users/internal/by-id/{user.id}"
            )
        if r.status_code not in (200, 204, 404):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"User service error: {r.status_code} {r.text}",
            )


def _jsonable(d: Dict[str, Any]) -> Dict[str, Any]:
    """Stringify UUIDs and other non-JSON types before sending."""
    out: Dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, uuid.UUID):
            out[k] = str(v)
        else:
            out[k] = v
    return out


async def get_user_db() -> AsyncGenerator[HTTPUserDatabase, None]:
    yield HTTPUserDatabase()


# ---------------------------------------------------------------------------
# UserManager
# ---------------------------------------------------------------------------
# Encapsulates password hashing, registration, and lookup. Override the
# on_after_* hooks to add audit logging or email verification later.

class UserManager(UUIDIDMixin, BaseUserManager[AuthUser, uuid.UUID]):
    reset_password_token_secret = AUTH_SECRET
    verification_token_secret   = AUTH_SECRET

    async def on_after_register(self, user: AuthUser, request=None):
        print(f"[auth-service] registered user {user.email} ({user.role})")


async def get_user_manager(
    user_db: HTTPUserDatabase = Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db)


# ---------------------------------------------------------------------------
# JWT strategy
# ---------------------------------------------------------------------------
# The default fastapi-users JWT carries only `sub` and `aud`. We override
# write_token to also embed `role`, `name`, `email` so peer services can
# authorize without an extra HTTP call back here for every request.

class RoleAwareJWTStrategy(JWTStrategy):
    async def write_token(self, user: AuthUser) -> str:
        data = {
            "sub": str(user.id),
            "aud": self.token_audience,
            "role": user.role,
            "name": user.name,
            "email": user.email,
        }
        return generate_jwt(
            data,
            self.encode_key,
            self.lifetime_seconds,
            algorithm=self.algorithm,
        )


def get_jwt_strategy() -> RoleAwareJWTStrategy:
    return RoleAwareJWTStrategy(
        secret=AUTH_SECRET, lifetime_seconds=JWT_LIFETIME_SECONDS
    )


bearer_transport = BearerTransport(tokenUrl="auth/login")

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


fastapi_users = FastAPIUsers[AuthUser, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)


# ---------------------------------------------------------------------------
# Refresh tokens
# ---------------------------------------------------------------------------
# Opaque random strings stored hashed (SHA-256). Single-use: every
# /auth/refresh revokes the presented token and issues a new one.

def _hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def issue_refresh_token(session: AsyncSession, user: AuthUser) -> str:
    """Create a new refresh-token row for `user` and return the raw value."""
    raw = secrets.token_urlsafe(48)
    row = RefreshToken(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=_hash_refresh_token(raw),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=REFRESH_LIFETIME_SECONDS),
        revoked=False,
    )
    session.add(row)
    await session.commit()
    return raw


async def rotate_refresh_token(
    session: AsyncSession, raw: str
) -> Optional[Tuple[str, AuthUser]]:
    """Validate `raw`, revoke it, and issue a replacement.

    Returns (new_raw, user) on success or None if the token is unknown,
    expired, already revoked, or the user can no longer be loaded.
    """
    if not raw:
        return None
    token_hash = _hash_refresh_token(raw)
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    row = result.scalar_one_or_none()
    if row is None or row.revoked:
        return None
    if row.expires_at <= datetime.now(timezone.utc):
        return None

    # Resolve the user via service-user. Refusing rotation when the user
    # has been deactivated is enforced here, not at the database layer.
    user_db = HTTPUserDatabase()
    user = await user_db.get(row.user_id)
    if user is None or not user.is_active:
        return None

    row.revoked = True
    new_raw = await issue_refresh_token(session, user)
    return new_raw, user


async def revoke_refresh_token(session: AsyncSession, raw: str) -> None:
    """Mark the refresh token as revoked. Silent no-op if not found."""
    if not raw:
        return
    token_hash = _hash_refresh_token(raw)
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .values(revoked=True)
    )
    await session.commit()
