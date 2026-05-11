from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PresignUploadRequest(BaseModel):
    """Request body for POST /files/presign-upload.

    storagePrefix lets the caller organise blobs by domain (e.g.
    "submissions/{assignmentId}/{studentId}/{submissionId}"). The final
    storage_key is "<prefix>/<fileRefId>/<name>" so collisions are
    impossible.
    """

    name: str
    contentType: str = Field(alias="content_type")
    sizeBytes: Optional[int] = Field(default=None, alias="size_bytes")
    storagePrefix: Optional[str] = Field(default=None, alias="storage_prefix")
    bucket: Optional[str] = None

    model_config = {"populate_by_name": True}


class PresignUploadResponse(BaseModel):
    fileRefId: UUID
    uploadUrl: str
    storageKey: str
    bucket: str

    model_config = {"populate_by_name": True}


class FileRefResponse(BaseModel):
    """Public view of a FileRef including a presigned GET URL.

    url is null while status is "pending". After confirmation it is a
    presigned URL valid for 1 hour.
    """

    id: UUID
    name: str
    sizeBytes: Optional[int] = Field(default=None, alias="size_bytes")
    contentType: str = Field(alias="content_type")
    status: str
    url: Optional[str] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class BatchFilesRequest(BaseModel):
    ids: list[UUID]


class FileMetaInternal(BaseModel):
    id: UUID
    name: str
    sizeBytes: Optional[int] = Field(default=None, alias="size_bytes")
    contentType: str = Field(alias="content_type")
    status: str
    createdAt: datetime = Field(alias="created_at")

    model_config = {"from_attributes": True, "populate_by_name": True}
