# Submission ORM models.
#
# File bytes and FileRef metadata live in service-file-storage.
# This service only tracks which FileRef ids belong to which
# submission, and enriches reads via peer calls.

from uuid import uuid4

from sqlalchemy import UUID, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign references to assignment and student — plain UUIDs,
    # no FK constraints since those records live in other services.
    assignment_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # studentName denormalized to avoid a user-service hop on every read.
    student_name = Column(String, nullable=False)

    submitted_at = Column(DateTime, server_default=func.now())

    # Submission lifecycle: submitted | graded | returned
    status = Column(String, nullable=False, default="submitted")

    files = relationship(
        "SubmissionFile",
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="SubmissionFile.position",
    )


class SubmissionFile(Base):
    """Link to a FileRef owned by service-file-storage.

    Only the FileRef id and the user-visible filename are stored locally.
    contentType / sizeBytes / url come from a peer call at read time.
    """

    __tablename__ = "submission_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    submission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id"),
        nullable=False,
        index=True,
    )
    # The FileRef id in service-file-storage. No FK constraint — it
    # lives in a different database.
    file_ref_id = Column(UUID(as_uuid=True), nullable=False)
    # Denormalized so we can still render filenames if the file-storage
    # peer call fails (UX fallback only).
    name = Column(String, nullable=False)
    position = Column(Integer, nullable=False, default=0)

    submission = relationship("Submission", back_populates="files")
