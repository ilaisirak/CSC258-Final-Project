from datetime import timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, get_current_user
from app.config import DEFAULT_BUCKET
from app.database import get_db
from app.models import FileRef, FileStatus
from app.schemas import (
    FileRefResponse,
    PresignUploadRequest,
    PresignUploadResponse,
)
from app.storage import ensure_bucket, internal_client, public_client

router = APIRouter()

_GET_URL_EXPIRY = timedelta(hours=1)
_PUT_URL_EXPIRY = timedelta(minutes=15)


@router.post(
    "/files/presign-upload",
    response_model=PresignUploadResponse,
    status_code=201,
)
async def presign_upload(
    body: PresignUploadRequest,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> PresignUploadResponse:
    """Create a pending FileRef and return a presigned PUT URL.

    The presigned URL is signed with the public MinIO endpoint so the
    browser can PUT directly. The FileRef row stays in `pending` state
    until the caller hits /confirm. If the browser never PUTs, the row
    is orphaned (no MinIO object exists) and eventually pruned.
    """
    bucket = body.bucket or DEFAULT_BUCKET
    ensure_bucket(bucket)

    file_ref = FileRef(
        bucket=bucket,
        storage_key="",  # set below once we know the id
        name=body.name,
        content_type=body.contentType,
        size_bytes=body.sizeBytes,
        status=FileStatus.pending,
    )
    db.add(file_ref)
    await db.flush()

    prefix = body.storagePrefix.strip("/") if body.storagePrefix else "uploads"
    storage_key = f"{prefix}/{file_ref.id}/{body.name}"
    file_ref.storage_key = storage_key

    upload_url = public_client().presigned_put_object(
        bucket,
        storage_key,
        expires=_PUT_URL_EXPIRY,
    )

    await db.commit()

    return PresignUploadResponse(
        fileRefId=file_ref.id,
        uploadUrl=upload_url,
        storageKey=storage_key,
        bucket=bucket,
    )


@router.post("/files/{file_ref_id}/confirm", response_model=FileRefResponse)
async def confirm_upload(
    file_ref_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> FileRefResponse:
    """Mark a FileRef as committed once the browser has PUT the bytes.

    Verifies the object actually exists in MinIO before marking
    committed, so we never report a confirmed FileRef whose bytes are
    missing.
    """
    file_ref = (
        await db.execute(select(FileRef).where(FileRef.id == file_ref_id))
    ).scalar_one_or_none()
    if not file_ref:
        raise HTTPException(status_code=404, detail="FileRef not found")
    if file_ref.status == FileStatus.committed:
        return _to_response(file_ref, with_url=True)

    try:
        stat = internal_client().stat_object(file_ref.bucket, file_ref.storage_key)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=409,
            detail=f"Object not found in storage: {exc}",
        ) from exc

    if file_ref.size_bytes is None:
        file_ref.size_bytes = stat.size
    file_ref.status = FileStatus.committed
    await db.commit()
    await db.refresh(file_ref)

    return _to_response(file_ref, with_url=True)


@router.get("/files/{file_ref_id}", response_model=FileRefResponse)
async def get_file(
    file_ref_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> FileRefResponse:
    file_ref = (
        await db.execute(select(FileRef).where(FileRef.id == file_ref_id))
    ).scalar_one_or_none()
    if not file_ref:
        raise HTTPException(status_code=404, detail="FileRef not found")
    return _to_response(file_ref, with_url=True)


@router.get("/files", response_model=list[FileRefResponse])
async def list_files(
    ids: Optional[str] = Query(default=None, description="Comma-separated UUIDs"),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> list[FileRefResponse]:
    """Batch lookup. Returns presigned GET URL for each committed FileRef."""
    if not ids:
        return []
    try:
        id_list = [UUID(x) for x in ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID in ids")

    rows = (
        await db.execute(select(FileRef).where(FileRef.id.in_(id_list)))
    ).scalars().all()

    return [_to_response(r, with_url=True) for r in rows]


def _to_response(file_ref: FileRef, with_url: bool) -> FileRefResponse:
    url: Optional[str] = None
    if with_url and file_ref.status == FileStatus.committed:
        url = public_client().presigned_get_object(
            file_ref.bucket,
            file_ref.storage_key,
            expires=_GET_URL_EXPIRY,
        )
    return FileRefResponse(
        id=file_ref.id,
        name=file_ref.name,
        size_bytes=file_ref.size_bytes,
        content_type=file_ref.content_type,
        status=file_ref.status.value if hasattr(file_ref.status, "value") else str(file_ref.status),
        url=url,
    )
