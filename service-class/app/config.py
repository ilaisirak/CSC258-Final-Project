import os

STORAGE_TYPE = os.getenv("STORAGE_TYPE", "minio")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

GCS_BUCKET = os.getenv("GCS_BUCKET", "your-bucket")

'''
Establishes the database connection URL, 
defaults to a local PostgreSQL instance if not set in the environment.

The URL format is:
postgresql+asyncpg://<username>:<password>@<host>:<port>/<database
'''
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://dev:devpassword@postgres-assignments:5432/assignments"
)