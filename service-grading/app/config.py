import os

# Establishes the database connection URL, defaults to a local PostgreSQL instance if not set in the environment.
# The URL format is:
# postgresql+asyncpg://<username>:<password>@<host>:<port>/<database>
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://dev:devpassword@postgres-assignments:5432/assignments"
)