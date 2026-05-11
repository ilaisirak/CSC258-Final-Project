# Pydantic models for request validation and response serialization.

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

SubmissionStatus = Literal["submitted", "graded", "returned"]


class FileRefResponse(BaseModel):
    """File metadata enriched from service-file-storage at read time.

    fileRefId is the stable id in service-file-storage. id (when present)
    refers to the SubmissionFile link row in this service — used by SPA
    code only for stable rendering keys.
    """

    fileRefId: UUID = Field(alias="file_ref_id")
    id: Optional[UUID] = None
    name: str
    sizeBytes: Optional[int] = Field(default=None, alias="size_bytes")
    contentType: Optional[str] = Field(default=None, alias="content_type")
    url: Optional[str] = None

    model_config = {"populate_by_name": True}


class GradeInline(BaseModel):
    """Slim grade view embedded in SubmissionResponse so the SPA can
    render graded state without a separate fan-out call.

    Mirrors the GradeResponse contract from service-grade-records but
    lives here to avoid a hard import dependency."""

    id: UUID
    submissionId: UUID = Field(alias="submission_id")
    score: float
    pointsPossible: float = Field(alias="points_possible")
    feedback: Optional[str] = None
    gradedById: UUID = Field(alias="graded_by_id")
    gradedAt: datetime = Field(alias="graded_at")

    model_config = {"populate_by_name": True}


class SubmissionResponse(BaseModel):
    id: UUID
    assignmentId: UUID = Field(alias="assignment_id")
    studentId: UUID = Field(alias="student_id")
    studentName: str = Field(alias="student_name")
    submittedAt: datetime = Field(alias="submitted_at")
    status: SubmissionStatus
    files: list[FileRefResponse] = []
    grade: Optional[GradeInline] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


# ─── Request bodies for the multi-step upload flow ───────────────────


class FileToUpload(BaseModel):
    """One entry in the create-submission request describing a file the
    SPA intends to upload."""

    name: str
    contentType: str = Field(alias="content_type")
    sizeBytes: Optional[int] = Field(default=None, alias="size_bytes")

    model_config = {"populate_by_name": True}


class CreateSubmissionRequest(BaseModel):
    assignmentId: UUID = Field(alias="assignment_id")
    files: list[FileToUpload]

    model_config = {"populate_by_name": True}


class CreateSubmissionFileResponse(BaseModel):
    """Element of CreateSubmissionResponse.files — one per uploaded file.

    The SPA receives the presigned PUT URL and uploads the bytes directly
    to MinIO, then calls /submissions/{id}/files/confirm to finalize.
    """

    fileRefId: UUID
    submissionFileId: UUID
    name: str
    uploadUrl: str

    model_config = {"populate_by_name": True}


class CreateSubmissionResponse(BaseModel):
    id: UUID
    assignmentId: UUID
    studentId: UUID
    files: list[CreateSubmissionFileResponse]

    model_config = {"populate_by_name": True}


class ConfirmFilesRequest(BaseModel):
    fileRefIds: list[UUID] = Field(alias="file_ref_ids")

    model_config = {"populate_by_name": True}
