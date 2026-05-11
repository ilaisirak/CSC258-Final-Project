# Refresh-token table.
#
# Refresh tokens are opaque random strings handed back to the browser in
# an HttpOnly cookie. We persist only their SHA-256 hash so a database
# leak does not expose live session credentials. Tokens are single-use:
# every /auth/refresh revokes the row and inserts a new one (rotation),
# which lets us detect token theft — if a revoked token is replayed, all
# sessions for that user can be invalidated.
#
# Note: user_id is a plain UUID with NO foreign-key constraint. The
# users table lives in a different database (service-user). Cross-service
# referential integrity is not enforced at the database layer.

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id         = Column(UUID(as_uuid=True), primary_key=True)
    user_id    = Column(UUID(as_uuid=True), nullable=False, index=True)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked    = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
