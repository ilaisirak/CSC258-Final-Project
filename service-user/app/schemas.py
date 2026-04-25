from pydantic import BaseModel, EmailStr
from typing import Literal, Optional
from uuid import UUID

Role = Literal["student", "professor"]

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role: Role

class UserSignIn(BaseModel):
    role: Role
    name: str

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role: Role

    model_config = {"from_attributes": True}