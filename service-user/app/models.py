# User ORM model.
#
# This service owns the users table — profile data plus the bcrypt
# hashed_password column. Password hashing happens in service-auth (the
# only service that knows AUTH_SECRET); we just store the hash that
# service-auth provides on registration.
#
# The columns mirror the historical fastapi-users base table so the
# schema is byte-compatible with existing dev/prod databases — we have
# only dropped the fastapi-users dependency, not changed the storage.

import uuid

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email           = Column(String(320), nullable=False, unique=True, index=True)
    hashed_password = Column(String(1024), nullable=False)
    is_active       = Column(Boolean, nullable=False, default=True)
    is_superuser    = Column(Boolean, nullable=False, default=False)
    is_verified     = Column(Boolean, nullable=False, default=False)

    name            = Column(String, nullable=False)

    # "student" | "professor" — enforced at the schema layer.
    role            = Column(String, nullable=False)

    created_at      = Column(DateTime, server_default=func.now())