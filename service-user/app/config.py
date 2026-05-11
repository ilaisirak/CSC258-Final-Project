import os

# Database connection URL. service-user owns the users table.
# Format: postgresql+asyncpg://<user>:<pass>@<host>:<port>/<db>
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://dev:devpassword@postgres-user:5432/user"
)
