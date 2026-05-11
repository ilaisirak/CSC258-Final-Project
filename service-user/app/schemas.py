# Pydantic schemas for the user service.
#
# Two layers of schemas live here:
#   - public: returned to the SPA / peer services. Excludes credential
#     columns.
#   - internal: returned only to service-auth on the /users/internal/*
#     endpoints (cluster-internal mTLS only). Carries hashed_password.

import uuid
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr

# Valid user roles — enforced at the schema layer.
Role = Literal["student", "professor"]


class UserPublic(BaseModel):
    """Public user shape — never includes credential fields."""
    id: uuid.UUID
    name: str
    email: str
    role: Role

    model_config = {"from_attributes": True}


class UserRead(BaseModel):
    """Profile shape returned by GET /users/me."""
    id: uuid.UUID
    email: EmailStr
    name: str
    role: Role
    is_active: bool = True

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Body of PATCH /users/me — name only for now."""
    name: Optional[str] = None


# ---------------------------------------------------------------------------
# Internal schemas — only consumed by service-auth over mTLS.
# ---------------------------------------------------------------------------

class UserInternal(BaseModel):
    """Full user row including the bcrypt hashed_password.

    Returned to service-auth so it can verify credentials. Must NEVER
    be serialized into a response that leaves the cluster.
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


class UserInternalCreate(BaseModel):
    """Body of POST /users/internal — sent by service-auth on register.

    The password has already been hashed by service-auth's UserManager.
    """
    email: EmailStr
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    name: str
    role: Role


class UserInternalUpdate(BaseModel):
    """Body of PATCH /users/internal/by-id/{id}."""
    email: Optional[EmailStr] = None
    hashed_password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None
    name: Optional[str] = None
    role: Optional[Role] = None