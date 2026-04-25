from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class GradeUpsert(BaseModel):
    submissionId: str
    score: float
    pointsPossible: float
    feedback: Optional[str] = None
    gradedById: str

class GradeResponse(BaseModel):
    id: str
    submissionId: str
    score: float
    pointsPossible: float
    feedback: Optional[str]
    gradedById: str
    gradedAt: datetime

    model_config = {"from_attributes": True}