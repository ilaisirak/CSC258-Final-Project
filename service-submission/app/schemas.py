# Pydantic models for request validation and response serialization.
# Field names use camelCase to match the frontend API contract.

from pydantic import BaseModel, Field
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime

SubmissionStatus = Literal["submitted", "graded", "returned"]


# Represents a single uploaded file attached to a submission.
class FileRefResponse(BaseModel):
    id: UUID
    name: str
    sizeBytes: int = Field(alias="size_bytes")
    contentType: str = Field(alias="content_type")
    url: Optional[str] = None

    model_config = {"from_attributes": True, "populate_by_name": True, "by_alias": True}


# Shapes the response returned by all submission endpoints.
# The grade field is intentionally absent — it is fetched separately
# from the grading service when needed by the frontend.
class SubmissionResponse(BaseModel):
    id: UUID
    assignmentId: UUID = Field(alias="assignment_id")
    studentId: UUID = Field(alias="student_id")
    studentName: str = Field(alias="student_name")
    submittedAt: datetime = Field(alias="submitted_at")
    status: SubmissionStatus
    files: list[FileRefResponse] = []

    model_config = {"from_attributes": True, "populate_by_name": True, "by_alias": True}