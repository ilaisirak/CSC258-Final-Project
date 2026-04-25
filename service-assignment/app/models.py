from uuid import uuid4
from sqlalchemy import UUID, Boolean, Column, Float, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Assignment(Base):
    __tablename__ = "assignments"

    id                = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    class_id          = Column(UUID(as_uuid=True), nullable=False)
    title             = Column(String, nullable=False)
    description       = Column(String, nullable=False, default="")
    due_at            = Column(DateTime, nullable=True)
    points_possible   = Column(Float, nullable=False, default=100.0) 
    status            = Column(String, nullable=False, default="open") 
    allow_resubmission = Column(Boolean, nullable=False, default=True)
    created_at        = Column(DateTime, server_default=func.now())