from uuid import uuid4
from sqlalchemy import UUID, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Class(Base):
    __tablename__ = "classes"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    code           = Column(String, nullable=False)
    name           = Column(String, nullable=False)
    description    = Column(String)
    professor_id   = Column(UUID(as_uuid=True), nullable=False)
    professor_name = Column(String, nullable=False)
    term_season    = Column(String, nullable=False)
    term_year      = Column(Integer, nullable=False)
    term_starts_on = Column(String, nullable=False)
    term_ends_on   = Column(String, nullable=False)
    created_at     = Column(DateTime, server_default=func.now())