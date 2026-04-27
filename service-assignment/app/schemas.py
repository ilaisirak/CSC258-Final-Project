# Pydantic models used for request validation and response serialization.
# Field names use camelCase to match the frontend API contract.
# Aliases map camelCase fields to the snake_case column names in the ORM model.

from pydantic import BaseModel, Field
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime

# Valid lifecycle states for an assignment.
AssignmentStatus = Literal["draft", "open", "closed"]

# Validates the request body for POST /assignments.
# Field names are camelCase to match incoming JSON from the frontend.
class AssignmentCreate(BaseModel):
    classId: UUID
    title: str
    description: str = ""
    dueAt: Optional[datetime] = None
    pointsPossible: float = 100.0
    status: AssignmentStatus = "open"
    allowResubmission: bool = True

    model_config = {"from_attributes": True, "populate_by_name": True}

# Shapes the response returned by all assignment endpoints.
# Field aliases map ORM snake_case column names to camelCase JSON output.
# by_alias=True ensures the response serializes using the camelCase names.
class AssignmentResponse(BaseModel):
    id: UUID
    classId: UUID               = Field(alias="class_id")
    title: str
    description: str
    dueAt: Optional[datetime]   = Field(alias="due_at")
    pointsPossible: float       = Field(alias="points_possible")
    status: AssignmentStatus
    allowResubmission: bool     = Field(alias="allow_resubmission")

    model_config = {"from_attributes": True, "populate_by_name": True, "by_alias": True}