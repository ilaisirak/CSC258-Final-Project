# Pydantic models used for request validation and response serialization
# for the user service. All field names match the ORM model directly since
# user fields are single words with no camelCase/snake_case mismatch.

from pydantic import BaseModel, EmailStr
from typing import Literal, Optional
from uuid import UUID

# Valid user roles — enforced at the schema level so invalid roles are
# rejected before reaching the database.
Role = Literal["student", "professor"]

# Validates the request body for POST /users.
# EmailStr performs format validation on the email field,
# requiring email-validator to be installed in requirements.txt.
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role: Role

# Validates the request body for POST /users/sign-in.
# Sign-in currently matches by name and role rather than email and password.
# This is a development placeholder — see routes.py for details.
class UserSignIn(BaseModel):
    role: Role
    name: str

# Shapes the response returned by all user endpoints.
# No aliases are needed here since all field names are identical
# in both Python and JSON (id, name, email, role).
class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role: Role

    model_config = {"from_attributes": True}