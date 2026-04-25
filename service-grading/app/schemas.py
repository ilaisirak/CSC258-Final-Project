from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class GradeUpsert(BaseModel):
    submissionId: UUID = Field(alias="submission_id")
    score: float
    pointsPossible: float = Field(alias="points_possible")
    feedback: Optional[str] = None
    gradedById: UUID = Field(alias="graded_by_id")

    model_config = {"from_attributes": True, "populate_by_name": True}

class GradeResponse(BaseModel):
    id: UUID
    submissionId: UUID = Field(alias="submission_id")
    score: float
    pointsPossible: float = Field(alias="points_possible")
    feedback: Optional[str]
    gradedById: UUID = Field(alias="graded_by_id")
    gradedAt: datetime = Field(alias="graded_at")

    model_config = {"from_attributes": True, "populate_by_name": True}

class GradeUpdate(BaseModel):
    score: float
    feedback: Optional[str] = None