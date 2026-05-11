# HTTP endpoints owned by the user service.
#
# Two surfaces are exposed:
#
#   1. Public (gateway-facing) routes:
#        GET   /users                       (authenticated)
#        GET   /users/search                (authenticated)
#        GET   /users/by-id/{user_id}       (authenticated)
#        GET   /users/me                    (authenticated)
#        PATCH /users/me                    (authenticated)
#
#   2. Internal (service-auth-only) routes:
#        GET    /users/internal/by-email
#        GET    /users/internal/by-id/{user_id}
#        POST   /users/internal
#        PATCH  /users/internal/by-id/{user_id}
#        DELETE /users/internal/by-id/{user_id}
#
# Internal routes return the bcrypt hashed_password so service-auth can
# verify credentials. They MUST be reachable only over cluster-internal
# mTLS — the gateway does not proxy /users/internal/* to anyone.

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models import User
from app.schemas import (
    UserInternal,
    UserInternalCreate,
    UserInternalUpdate,
    UserPublic,
    UserRead,
    UserUpdate,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Public routes — used by the SPA and peer services
# ---------------------------------------------------------------------------

@router.get("/users/me", response_model=UserRead)
async def read_me(
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/me", response_model=UserRead)
async def update_me(
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.name is not None:
        user.name = body.name
    await db.commit()
    await db.refresh(user)
    return user


# Retrieve all registered users. Used by the professor-side class roster
# UI to suggest existing students.
@router.get("/users", response_model=list[UserPublic])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(select(User))
    return result.scalars().all()


# Search users by email or name. service-class calls this to resolve a
# student's UUID from the email a professor types into the roster form.
@router.get("/users/search", response_model=list[UserPublic])
async def search_users(
    email: str | None = None,
    name: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    query = select(User)
    if email:
        query = query.where(User.email == email)
    elif name:
        query = query.where(User.name.ilike(f"%{name}%"))
    result = await db.execute(query)
    return result.scalars().all()


# Resolve a single user by their UUID. Mounted at /users/by-id/{user_id}
# so it does not collide with /users/me.
@router.get("/users/by-id/{user_id}", response_model=UserPublic)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ---------------------------------------------------------------------------
# Internal routes — service-auth only, returns hashed_password
# ---------------------------------------------------------------------------
# Authorization model: cluster-internal mTLS guarantees the caller is
# another backend service holding a cert signed by our CA. Currently
# only service-auth has a legitimate need to call these. We do not add
# additional service-identity checks here — adding them is a planned
# future hardening step and would be implemented by inspecting the
# verified peer certificate CN.

internal_router = APIRouter(prefix="/users/internal", tags=["internal"])


@internal_router.get("/by-email", response_model=UserInternal)
async def internal_get_by_email(
    email: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@internal_router.get("/by-id/{user_id}", response_model=UserInternal)
async def internal_get_by_id(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@internal_router.post("", response_model=UserInternal, status_code=status.HTTP_201_CREATED)
async def internal_create(
    body: UserInternalCreate,
    db: AsyncSession = Depends(get_db),
):
    user = User(
        id=uuid.uuid4(),
        email=body.email,
        hashed_password=body.hashed_password,
        is_active=body.is_active,
        is_superuser=body.is_superuser,
        is_verified=body.is_verified,
        name=body.name,
        role=body.role,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    await db.refresh(user)
    return user


@internal_router.patch("/by-id/{user_id}", response_model=UserInternal)
async def internal_update(
    user_id: uuid.UUID,
    body: UserInternalUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    await db.refresh(user)
    return user


@internal_router.delete("/by-id/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def internal_delete(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return
    await db.delete(user)
    await db.commit()

