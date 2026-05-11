# FileRef ORM model.
#
# A FileRef tracks a single blob stored in object storage (MinIO). The
# row is created in `pending` state by the presign-upload endpoint and
# transitions to `committed` once the caller confirms a successful PUT
# from the browser. Pending rows older than a TTL can be reaped by an
# external sweeper (out of scope here).
#
# This service has no ownership concept: it stores the bytes and the
# metadata, and any consumer (e.g. service-submission) tracks the
# FileRef id in its own database.

import enum
import uuid

from sqlalchemy import UUID, Column, DateTime, Enum, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class FileStatus(str, enum.Enum):
    pending = "pending"
    committed = "committed"


class FileRef(Base):
    __tablename__ = "file_refs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bucket = Column(String, nullable=False)
    storage_key = Column(String, nullable=False)
    name = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=True)
    status = Column(
        Enum(FileStatus, name="file_status"),
        nullable=False,
        default=FileStatus.pending,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
