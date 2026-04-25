from uuid import uuid4
from sqlalchemy import UUID, Column, Float, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Grade(Base):
    __tablename__ = "grades"

    id              = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    submission_id   = Column(UUID(as_uuid=True), nullable=False)
    score           = Column(Float, nullable=False)  
    points_possible = Column(Float, nullable=False) 
    feedback        = Column(String, nullable=True)
    graded_by_id    = Column(UUID(as_uuid=True), nullable=False) 
    graded_at       = Column(DateTime, server_default=func.now())