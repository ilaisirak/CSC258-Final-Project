from uuid import uuid4

from sqlalchemy import UUID, Column, DateTime, UniqueConstraint
from sqlalchemy.sql import func

from app.database import Base


class Enrollment(Base):
    """Join row connecting a class (owned by service-class) and a
    student (owned by service-user). Neither id is a foreign key — the
    referenced rows live in other databases."""

    __tablename__ = "enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    class_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    enrolled_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("class_id", "student_id", name="uq_enrollment"),
    )
