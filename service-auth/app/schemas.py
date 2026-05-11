# Pydantic schemas for the auth service.
#
# AuthUser is the in-memory representation of a user record fetched from
# service-user. It carries everything the auth flow needs (incl. the
# bcrypt hashed_password) but is never exposed back to the SPA — the
# /auth/* responses return only access tokens and the lightweight user
# shape needed by the SPA.

import uuid
from typing import Literal, Optional

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr

Role = Literal["student", "professor"]


class AuthUser(BaseModel):
    """Internal user shape used by the fastapi-users UserManager.

    Mirrors the columns service-user exposes via its internal endpoints.
    """
    id: uuid.UUID
    email: str
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    name: str
    role: Role

    model_config = {"from_attributes": True}


# Inherit fastapi-users base schemas so the register router can call
# `create_update_dict()` and the JWT/cookie machinery can serialize
# responses the way the library expects.

class UserRead(schemas.BaseUser[uuid.UUID]):
    """Shape returned to the SPA after registration."""
    name: str
    role: Role


class UserCreate(schemas.BaseUserCreate):
    """Body of POST /auth/register."""
    name: str
    role: Role


class UserUpdate(schemas.BaseUserUpdate):
    """Body for password / profile updates. All fields optional."""
    name: Optional[str] = None
    role: Optional[Role] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
