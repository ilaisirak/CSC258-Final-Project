# Defines the HTTP endpoints for the submission service.
# Handles file uploads to MinIO and submission metadata storage in PostgreSQL.

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from app.database import get_db
from app.models import Submission, FileRef
from app.schemas import SubmissionResponse
from app.config import STORAGE_TYPE, MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY
from minio import Minio
import io

router = APIRouter()


def get_storage():
    """Returns a configured MinIO client."""
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


# Submit an assignment — accepts multipart form data with one or more files.
# Uploads each file to MinIO and stores submission metadata in the database.
@router.post("/submit", response_model=SubmissionResponse)
async def submit_assignment(
    assignmentId: UUID = Form(...),
    studentId: UUID = Form(...),
    studentName: str = Form(...),
    file: UploadFile = File(description="File to submit"),
    db: AsyncSession = Depends(get_db)
):
    client, bucket = get_storage()

    submission = Submission(
        assignment_id=assignmentId,
        student_id=studentId,
        student_name=studentName,
        status="submitted"
    )
    db.add(submission)
    await db.flush()

    data = await file.read()
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

    result = await db.execute(
        select(Submission)
        .where(Submission.id == submission.id)
        .options(selectinload(Submission.files))
    )
    return result.scalar_one()


# Retrieve a single submission by UUID.
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
    return submission


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
    return result.scalars().all()