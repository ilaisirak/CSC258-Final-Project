# Async SQLAlchemy engine + session factory for the refresh-token store.
# service-auth owns only the refresh_tokens table; user records live in
# service-user.

import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


# FastAPI dependency that opens a database session per request and
# automatically closes it when the request completes.
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
