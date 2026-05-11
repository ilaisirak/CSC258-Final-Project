# MinIO client helpers.
#
# Two distinct clients are needed:
#   1. internal_client — talks to MinIO over the cluster-internal DNS
#      (e.g. minio:9000). Used for bucket bootstrap, object existence
#      checks, and generating server-side presigned URLs that are
#      *intended* for browser consumption (so they must be signed with
#      the public host name, not the internal one).
#   2. public_client — same credentials, configured with the public
#      endpoint so the signed URL's Host header matches what the
#      browser will dial. Region is supplied explicitly to skip the
#      region lookup HTTP round-trip (which would fail since the public
#      endpoint is unreachable from inside the container).

from minio import Minio

from app.config import (
    DEFAULT_BUCKET,
    MINIO_ACCESS_KEY,
    MINIO_ENDPOINT,
    MINIO_PUBLIC_ENDPOINT,
    MINIO_PUBLIC_SECURE,
    MINIO_REGION,
    MINIO_SECRET_KEY,
    MINIO_SECURE,
)


def internal_client() -> Minio:
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
    )


def public_client() -> Minio:
    return Minio(
        MINIO_PUBLIC_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_PUBLIC_SECURE,
        region=MINIO_REGION,
    )


def ensure_bucket(bucket: str = DEFAULT_BUCKET) -> None:
    """Idempotently create the bucket if it doesn't exist."""
    c = internal_client()
    if not c.bucket_exists(bucket):
        c.make_bucket(bucket)
