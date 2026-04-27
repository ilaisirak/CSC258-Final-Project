# Pydantic models used for request validation and response serialization.
# Field names use camelCase to match the frontend API contract.
# Aliases map camelCase fields to the snake_case column names in the ORM model.

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

# Validates the request body for POST /grading.
# Used for both creating a new grade and updating an existing one,
# since the endpoint follows an upsert pattern.
class GradeUpsert(BaseModel):
    submissionId: UUID    = Field(alias="submission_id")
    score: float
    pointsPossible: float = Field(alias="points_possible")
    feedback: Optional[str] = None
    gradedById: UUID      = Field(alias="graded_by_id")

    model_config = {"from_attributes": True, "populate_by_name": True}

# Shapes the response returned by all grading endpoints.
# Field aliases map ORM snake_case column names to camelCase JSON output.
class GradeResponse(BaseModel):
    id: UUID
    submissionId: UUID    = Field(alias="submission_id")
    score: float
    pointsPossible: float = Field(alias="points_possible")
    feedback: Optional[str]
    gradedById: UUID      = Field(alias="graded_by_id")
    gradedAt: datetime    = Field(alias="graded_at")

    model_config = {"from_attributes": True, "populate_by_name": True}

# Validates the request body for PATCH /grading/{grade_id}.
# Intentionally limited to score and feedback — submission and grader
# references cannot be changed after a grade is created.
class GradeUpdate(BaseModel):
    score: float
    feedback: Optional[str] = None