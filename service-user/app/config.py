import os

STORAGE_TYPE = os.getenv("STORAGE_TYPE", "minio")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

GCS_BUCKET = os.getenv("GCS_BUCKET", "your-bucket")