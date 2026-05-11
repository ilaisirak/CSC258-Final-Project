# Configuration for service-file-storage.
#
# MINIO_ENDPOINT       — cluster-internal MinIO endpoint (e.g. minio:9000).
#                        Used by this service to upload and check objects.
# MINIO_PUBLIC_ENDPOINT — host the browser will use to PUT/GET MinIO
#                        objects via presigned URLs. Different from
#                        MINIO_ENDPOINT because the browser cannot resolve
#                        the in-cluster DNS name. Defaults to
#                        "localhost:9000" for docker-compose.
#                        Must be set explicitly in k8s to a routable host.
# MINIO_PUBLIC_SECURE  — "true" if the public endpoint serves https.

import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://dev:devpassword@postgres-file-storage:5432/file_storage",
)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

MINIO_PUBLIC_ENDPOINT = os.getenv("MINIO_PUBLIC_ENDPOINT", "localhost:9000")
MINIO_PUBLIC_SECURE = os.getenv("MINIO_PUBLIC_SECURE", "false").lower() == "true"
# Some MinIO regions complain when not set; the URL signature is region-aware.
MINIO_REGION = os.getenv("MINIO_REGION", "us-west-1")

DEFAULT_BUCKET = os.getenv("FILE_STORAGE_BUCKET", "submissions")
