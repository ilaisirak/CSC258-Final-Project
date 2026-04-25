from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name       = Column(String, nullable=False)
    email      = Column(String, nullable=False, unique=True, index=True)
    role       = Column(String, nullable=False)  # "student" | "professor"
    created_at = Column(DateTime, server_default=func.now())