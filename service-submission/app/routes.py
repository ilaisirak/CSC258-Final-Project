# Defines the HTTP endpoints for the submission service.
# Handles file uploads to MinIO and submission metadata storage in PostgreSQL.

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from app.database import get_db
from app.models import Submission, FileRef
from app.schemas import SubmissionResponse, FileRefResponse
from app.config import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY
from minio import Minio
from datetime import timedelta
import io

router = APIRouter()

# Returns a configured MinIO client and bucket name.
def get_storage(): 
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
    bucket = "submissions"
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    return client, bucket

# Returns a MinIO client configured for localhost:9000.
# Used exclusively for generating pre-signed URLs that are
# accessible from the browser on the host machine.
# The region is provided directly to skip the region lookup HTTP call,
# which would fail since localhost:9000 is unreachable from inside Docker.
def get_public_client():
    return Minio(
        "localhost:9000",
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
        region="us-west-1"
    )

# Generates pre-signed URLs for each file ref and returns a list
# of dicts matching the FileRefResponse schema.
# Called on every submission read so the frontend receives populated
# URLs without needing a separate call per file.
def enrich_files(files: list, public_client: Minio, bucket: str) -> list[dict]:
    enriched = []
    for f in files:
        url = public_client.presigned_get_object(
            bucket,
            f.storage_key,
            expires=timedelta(hours=1)
        )
        enriched.append({
            "id": f.id,
            "name": f.name,
            "size_bytes": f.size_bytes,
            "content_type": f.content_type,
            "url": url
        })
    return enriched


# Submit an assignment — accepts multipart form data with a single file.
# Uploads the file to MinIO and stores submission metadata in the database.
@router.post("/submit", response_model=SubmissionResponse)
async def submit_assignment(
    assignmentId: UUID = Form(...),
    studentId: UUID = Form(...),
    studentName: str = Form(...),
    file: UploadFile = File(description="File to submit"),
    db: AsyncSession = Depends(get_db)
):
    client, bucket = get_storage()

    # Create the submission record first to get the UUID for the storage key.
    submission = Submission(
        assignment_id=assignmentId,
        student_id=studentId,
        student_name=studentName,
        status="submitted"
    )
    db.add(submission)
    await db.flush()

    data = await file.read()

    # Store under a structured path for readability in the MinIO console.
    # Format: submissions/{assignmentId}/{studentId}/{submissionId}/{filename}
    storage_key = f"submissions/{assignmentId}/{studentId}/{submission.id}/{file.filename}"

    client.put_object(
        bucket,
        storage_key,
        io.BytesIO(data),
        length=len(data),
        content_type=file.content_type or "application/octet-stream"
    )

    file_ref = FileRef(
        submission_id=submission.id,
        name=file.filename,
        size_bytes=len(data),
        content_type=file.content_type or "application/octet-stream",
        storage_key=storage_key
    )
    db.add(file_ref)

    await db.commit()
    await db.refresh(submission)

    # Reload with files relationship populated, then enrich with URLs.
    result = await db.execute(
        select(Submission)
        .where(Submission.id == submission.id)
        .options(selectinload(Submission.files))
    )
    submission = result.scalar_one()
    public_client = get_public_client()
    enriched = enrich_files(submission.files, public_client, bucket)

    return SubmissionResponse(
        id=submission.id,
        assignment_id=submission.assignment_id,
        student_id=submission.student_id,
        student_name=submission.student_name,
        submitted_at=submission.submitted_at,
        status=submission.status,
        files=[FileRefResponse(**f) for f in enriched]
    )


# Generate a pre-signed URL for a single file ref by its UUID.
# Useful for refreshing an expired URL without re-fetching the full submission.
@router.get("/submissions/file/{file_ref_id}")
async def get_file_url(file_ref_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FileRef).where(FileRef.id == file_ref_id)
    )
    file_ref = result.scalar_one_or_none()
    if not file_ref:
        raise HTTPException(status_code=404, detail="File not found")

    _, bucket = get_storage()
    public_client = get_public_client()

    url = public_client.presigned_get_object(
        bucket,
        file_ref.storage_key,
        expires=timedelta(hours=1)
    )

    return {"url": url, "name": file_ref.name, "contentType": file_ref.content_type}


# Retrieve a single submission by UUID with pre-signed file URLs populated.
# Returns 404 if not found.
@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
async def get_submission(submission_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Submission)
        .where(Submission.id == submission_id)
        .options(selectinload(Submission.files))
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    _, bucket = get_storage()
    public_client = get_public_client()
    enriched = enrich_files(submission.files, public_client, bucket)

    return SubmissionResponse(
        id=submission.id,
        assignment_id=submission.assignment_id,
        student_id=submission.student_id,
        student_name=submission.student_name,
        submitted_at=submission.submitted_at,
        status=submission.status,
        files=[FileRefResponse(**f) for f in enriched]
    )


# Retrieve submissions filtered by assignmentId or studentId.
# assignmentId — used by the grading service to list all submissions for an assignment.
# studentId    — used by the student dashboard to show submission history.
@router.get("/submissions", response_model=list[SubmissionResponse])
async def get_submissions(
    assignmentId: str = None,
    studentId: str = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Submission).options(selectinload(Submission.files))
    if assignmentId:
        query = query.where(Submission.assignment_id == assignmentId)
    if studentId:
        query = query.where(Submission.student_id == studentId)
    result = await db.execute(query)
    submissions = result.scalars().all()

    _, bucket = get_storage()
    public_client = get_public_client()

    # Enrich all submissions with pre-signed URLs in a single pass.
    responses = []
    for submission in submissions:
        enriched = enrich_files(submission.files, public_client, bucket)
        responses.append(SubmissionResponse(
            id=submission.id,
            assignment_id=submission.assignment_id,
            student_id=submission.student_id,
            student_name=submission.student_name,
            submitted_at=submission.submitted_at,
            status=submission.status,
            files=[FileRefResponse(**f) for f in enriched]
        ))

    return responses