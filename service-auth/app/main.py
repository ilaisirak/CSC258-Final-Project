# Entry point for the auth service.
#
# Responsibilities:
#   - POST /auth/login          : exchange email+password for an access
#                                 token + refresh-cookie pair.
#   - POST /auth/refresh        : rotate the refresh cookie and return a
#                                 fresh access token.
#   - POST /auth/logout         : revoke the refresh token + clear cookie.
#   - GET  /auth/verify         : token introspection used by the gateway
#                                 to convert a bearer token into
#                                 X-Auth-User-* identity headers.
#   - POST /auth/register       : create a new user (proxies to
#                                 service-user with a hashed password).
#
# All credential storage and user CRUD lives in service-user. This service
# only persists refresh tokens.

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, FastAPI, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    current_active_user,
    fastapi_users,
    get_jwt_strategy,
    get_user_manager,
    issue_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
    UserManager,
)
from app.config import (
    REFRESH_COOKIE_NAME,
    REFRESH_COOKIE_PATH,
    REFRESH_COOKIE_SECURE,
    REFRESH_LIFETIME_SECONDS,
)
from app.database import Base, engine, get_db
from app.schemas import AuthUser, UserCreate, UserRead


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the refresh_tokens table on startup if it doesn't already
    # exist. service-auth owns no other tables.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


# ---------------------------------------------------------------------------
# Cookie helpers
# ---------------------------------------------------------------------------

def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_token,
        max_age=REFRESH_LIFETIME_SECONDS,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=REFRESH_COOKIE_SECURE,
        samesite="lax",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
    )


# ---------------------------------------------------------------------------
# /auth/login, /auth/refresh, /auth/logout
# ---------------------------------------------------------------------------
# We deliberately do NOT mount fastapi_users.get_auth_router here. The
# library's router only knows about access tokens; we need login to also
# issue a refresh-token cookie and rotation/revocation endpoints.

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/login")
async def login(
    response: Response,
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager: UserManager = Depends(get_user_manager),
    db: AsyncSession = Depends(get_db),
):
    """Exchange email + password for an access token + refresh cookie."""
    user = await user_manager.authenticate(credentials)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LOGIN_BAD_CREDENTIALS",
        )

    strategy = get_jwt_strategy()
    access_token = await strategy.write_token(user)
    refresh_raw = await issue_refresh_token(db, user)
    _set_refresh_cookie(response, refresh_raw)

    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/refresh")
async def refresh(
    response: Response,
    db: AsyncSession = Depends(get_db),
    cookie_token: Optional[str] = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
):
    """Rotate the refresh cookie and return a fresh access token."""
    if not cookie_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh cookie")

    rotated = await rotate_refresh_token(db, cookie_token)
    if rotated is None:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    new_raw, user = rotated
    strategy = get_jwt_strategy()
    access_token = await strategy.write_token(user)
    _set_refresh_cookie(response, new_raw)
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    cookie_token: Optional[str] = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
):
    """Revoke the refresh token and clear the cookie."""
    if cookie_token:
        await revoke_refresh_token(db, cookie_token)
    _clear_refresh_cookie(response)


app.include_router(auth_router)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
# fastapi-users' standard register router calls UserManager.create which
# in turn calls our HTTPUserDatabase.create — so registration ultimately
# inserts the row inside service-user, with a freshly bcrypt-hashed
# password.

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)


# ---------------------------------------------------------------------------
# Token introspection — gateway-only
# ---------------------------------------------------------------------------
# nginx runs `auth_request /_auth_verify` on every protected /api/*
# request. On 200 it captures these X-Auth-User-* headers and injects
# them into the upstream request, so backends authorize without parsing
# the JWT themselves. Microservice equivalent of OAuth2 token
# introspection (RFC 7662).

@app.get("/auth/verify", tags=["auth"])
async def verify_token(response: Response, user: AuthUser = Depends(current_active_user)):
    response.headers["X-Auth-User-Id"]    = str(user.id)
    response.headers["X-Auth-User-Role"]  = user.role
    response.headers["X-Auth-User-Name"]  = user.name
    response.headers["X-Auth-User-Email"] = user.email
    return {
        "id": str(user.id),
        "role": user.role,
        "name": user.name,
        "email": user.email,
    }


# Health check used by Docker and Kubernetes readiness probes.
@app.get("/health")
def health():
    return {"status": "ok", "service": "service-auth"}
