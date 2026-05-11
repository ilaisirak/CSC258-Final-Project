import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://dev:devpassword@postgres-enrollment:5432/enrollment",
)
