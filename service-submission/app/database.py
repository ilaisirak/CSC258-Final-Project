
# Sets up the async database engine, session factory, and base model class
# for SQLAlchemy. Also provides the get_db dependency injected into routes.

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import DATABASE_URL

# Async engine — connects to PostgreSQL using the URL from config.
# echo=True logs all generated SQL statements to stdout during development.
engine = create_async_engine(DATABASE_URL, echo=True)

# Session factory — produces AsyncSession objects bound to the engine.
# expire_on_commit=False prevents SQLAlchemy from expiring ORM attributes
# after a commit, which avoids errors when accessing objects in async context.
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for all ORM models in this service.
class Base(DeclarativeBase):
    pass

# FastAPI dependency that opens a database session per request and
# automatically closes it when the request completes.
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session