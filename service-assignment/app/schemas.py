from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal

AssignmentStatus = Literal["draft", "open", "closed"]

class AssignmentCreate(BaseModel):
    classId: str
    title: str
    description: str = ""
    dueAt: Optional[datetime] = None
    pointsPossible: float = 100.0
    status: AssignmentStatus = "open"
    allowResubmission: bool = True

class AssignmentResponse(BaseModel):
    id: str
    classId: str
    title: str
    description: str
    dueAt: Optional[datetime]
    pointsPossible: float
    status: AssignmentStatus
    allowResubmission: bool

    model_config = {"from_attributes": True}