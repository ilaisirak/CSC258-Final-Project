from pydantic import BaseModel, Field
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime

AssignmentStatus = Literal["draft", "open", "closed"]

class AssignmentCreate(BaseModel):
    classId: UUID
    title: str
    description: str = ""
    dueAt: Optional[datetime] = None
    pointsPossible: float = 100.0
    status: AssignmentStatus = "open"
    allowResubmission: bool = True

    model_config = {"from_attributes": True, "populate_by_name": True}

class AssignmentResponse(BaseModel):
    id: UUID
    classId: UUID = Field(alias="class_id")
    title: str
    description: str
    dueAt: Optional[datetime] = Field(alias="due_at")
    pointsPossible: float = Field(alias="points_possible")
    status: AssignmentStatus
    allowResubmission: bool = Field(alias="allow_resubmission")

    model_config = {"from_attributes": True, "populate_by_name": True, "by_alias": True}