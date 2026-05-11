# HTTP endpoints for service-submission.
#
# This service stores only submission metadata and the list of FileRef
# ids that belong to each submission. File bytes and presigned URLs
# are owned by service-file-storage and fetched at read time via mTLS
# peer calls.
#
# Upload flow (browser-driven, 3 calls + 1 direct PUT to MinIO):
#   1. SPA POST /submissions   → creates Submission + SubmissionFile
#                                rows and proxies presign-upload calls
#                                to file-storage. Returns upload URLs.
#   2. SPA PUT  <uploadUrl>     → bytes go straight to MinIO.
#   3. SPA POST /submissions/{id}/files/confirm
#                              → service-submission calls file-storage
#                                /files/{id}/confirm for each.

from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import CurrentUser, get_current_user, require_role
from app.database import get_db
from app.models import Submission, SubmissionFile
from app.peer import (
    ASSIGNMENT_SERVICE_URL,
    FILE_STORAGE_SERVICE_URL,
    GRADING_SERVICE_URL,
    mtls_client,
)
from app.schemas import (
    ConfirmFilesRequest,
    CreateSubmissionFileResponse,
    CreateSubmissionRequest,
    CreateSubmissionResponse,
    FileRefResponse,
    GradeInline,
    SubmissionResponse,
)

router = APIRouter()


def _forward_identity_headers(request: Request) -> dict[str, str]:
    """Forward the gateway-injected identity headers to peer services."""
    headers: dict[str, str] = {}
    for h in (
        "x-auth-user-id",
        "x-auth-user-role",
        "x-auth-user-name",
        "x-auth-user-email",
    ):
        v = request.headers.get(h)
        if v:
            headers[h] = v
    return headers


# ───────────────── upload flow ──────────────────


@router.post(
    "/submissions",
    response_model=CreateSubmissionResponse,
    status_code=201,
)
async def create_submission(
    body: CreateSubmissionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role("student")),
):
    """Create a submission and obtain presigned PUT URLs from file-storage.

    The submission row is created up front so that the FileRef ids can
    reference it. If presign fails partway through, the submission row
    stays but contains only the successfully presigned files; the
    confirm step on the SPA side reconciles.
    """
    if not body.files:
        raise HTTPException(status_code=400, detail="At least one file is required")

    headers = _forward_identity_headers(request)

    # Verify the assignment exists and is open before accepting a
    # submission. service-assignment is the authority on the lifecycle
    # (status + due date). Also enforce one-submission-per-(assignment,
    # student) unless the assignment allows resubmission.
    async with mtls_client() as client:
        a_res = await client.get(
            f"{ASSIGNMENT_SERVICE_URL}/assignments/{body.assignmentId}",
            headers=headers,
        )
    if a_res.status_code == 404:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if a_res.status_code != 200:
        raise HTTPException(status_code=502, detail="Assignment service error")
    assignment = a_res.json()
    if not assignment.get("isOpen"):
        raise HTTPException(
            status_code=403,
            detail="Assignment is not open for submission",
        )

    allow_resubmission = bool(assignment.get("allowResubmission"))
    if not allow_resubmission:
        existing = await db.execute(
            select(Submission).where(
                Submission.assignment_id == body.assignmentId,
                Submission.student_id == UUID(user.id),
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="Already submitted for this assignment",
            )

    submission = Submission(
        assignment_id=body.assignmentId,
        student_id=UUID(user.id),
        student_name=user.name or "",
        status="submitted",
    )
    db.add(submission)
    await db.flush()

    storage_prefix = (
        f"submissions/{body.assignmentId}/{user.id}/{submission.id}"
    )

    presigned: list[CreateSubmissionFileResponse] = []
    async with mtls_client() as client:
        for position, file_in in enumerate(body.files):
            res = await client.post(
                f"{FILE_STORAGE_SERVICE_URL}/files/presign-upload",
                headers=headers,
                json={
                    "name": file_in.name,
                    "contentType": file_in.contentType,
                    "sizeBytes": file_in.sizeBytes,
                    "storagePrefix": storage_prefix,
                },
            )
            if res.status_code != 201:
                raise HTTPException(
                    status_code=502,
                    detail=f"file-storage presign failed: {res.text}",
                )
            payload = res.json()
            link = SubmissionFile(
                id=uuid4(),
                submission_id=submission.id,
                file_ref_id=UUID(payload["fileRefId"]),
                name=file_in.name,
                position=position,
            )
            db.add(link)
            presigned.append(
                CreateSubmissionFileResponse(
                    fileRefId=UUID(payload["fileRefId"]),
                    submissionFileId=link.id,
                    name=file_in.name,
                    uploadUrl=payload["uploadUrl"],
                )
            )

    await db.commit()

    return CreateSubmissionResponse(
        id=submission.id,
        assignmentId=submission.assignment_id,
        studentId=submission.student_id,
        files=presigned,
    )


@router.post(
    "/submissions/{submission_id}/files/confirm",
    response_model=SubmissionResponse,
)
async def confirm_submission_files(
    submission_id: UUID,
    body: ConfirmFilesRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role("student")),
):
    """Tell file-storage that the browser has finished PUT-ing.

    The SPA passes the set of FileRef ids it successfully uploaded.
    The submission is then returned in its enriched form.
    """
    submission = await _load_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if str(submission.student_id) != user.id:
        raise HTTPException(status_code=403, detail="Not your submission")

    submission_ref_ids = {f.file_ref_id for f in submission.files}
    headers = _forward_identity_headers(request)

    async with mtls_client() as client:
        for fid in body.fileRefIds:
            if fid not in submission_ref_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"FileRef {fid} not in submission",
                )
            res = await client.post(
                f"{FILE_STORAGE_SERVICE_URL}/files/{fid}/confirm",
                headers=headers,
            )
            if res.status_code >= 400:
                raise HTTPException(
                    status_code=502,
                    detail=f"file-storage confirm failed: {res.text}",
                )

    return await _enrich_submission(submission, headers)


# ───────────────── read endpoints ───────────────


@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    submission = await _load_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return await _enrich_submission(
        submission, _forward_identity_headers(request)
    )


@router.get("/submissions", response_model=list[SubmissionResponse])
async def list_submissions(
    request: Request,
    assignmentId: Optional[str] = None,
    studentId: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    query = select(Submission).options(selectinload(Submission.files))
    if assignmentId:
        query = query.where(Submission.assignment_id == assignmentId)
    if studentId:
        query = query.where(Submission.student_id == studentId)
    submissions = (await db.execute(query)).scalars().all()

    headers = _forward_identity_headers(request)
    # Fetch all FileRefs in one batch call.
    all_ids = [str(f.file_ref_id) for s in submissions for f in s.files]
    file_meta = await _fetch_file_meta_batch(all_ids, headers)
    grade_by_sub = await _fetch_grades_batch(
        [str(s.id) for s in submissions], headers
    )
    return [_build_response(s, file_meta, grade_by_sub) for s in submissions]


@router.get("/submissions/file/{file_ref_id}")
async def get_file_url(
    file_ref_id: UUID,
    request: Request,
    _: CurrentUser = Depends(get_current_user),
):
    """Single-file lookup. Returns the presigned GET URL from file-storage."""
    headers = _forward_identity_headers(request)
    async with mtls_client() as client:
        res = await client.get(
            f"{FILE_STORAGE_SERVICE_URL}/files/{file_ref_id}",
            headers=headers,
        )
        if res.status_code == 404:
            raise HTTPException(status_code=404, detail="File not found")
        if res.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"file-storage error: {res.text}",
            )
    payload = res.json()
    return {
        "url": payload.get("url"),
        "name": payload.get("name"),
        "contentType": payload.get("contentType"),
    }


# ───────────────── helpers ──────────────────────


async def _load_submission(
    db: AsyncSession, submission_id: UUID
) -> Optional[Submission]:
    return (
        await db.execute(
            select(Submission)
            .where(Submission.id == submission_id)
            .options(selectinload(Submission.files))
        )
    ).scalar_one_or_none()


async def _fetch_file_meta_batch(
    ids: list[str], headers: dict[str, str]
) -> dict[str, dict]:
    """Return a {fileRefId -> meta} map from service-file-storage."""
    if not ids:
        return {}
    async with mtls_client() as client:
        res = await client.get(
            f"{FILE_STORAGE_SERVICE_URL}/files",
            params={"ids": ",".join(ids)},
            headers=headers,
        )
    if res.status_code >= 400:
        return {}
    return {item["id"]: item for item in res.json()}


async def _fetch_grades_batch(
    submission_ids: list[str], headers: dict[str, str]
) -> dict[str, dict]:
    """Return a {submissionId -> grade dict} map from service-grade-records.

    Uses the ?submissionIds= batch endpoint so this call does not recurse
    back into submissions (which the ?studentId= path would).
    """
    if not submission_ids:
        return {}
    async with mtls_client() as client:
        res = await client.get(
            f"{GRADING_SERVICE_URL}/grading",
            params={"submissionIds": ",".join(submission_ids)},
            headers=headers,
        )
    if res.status_code >= 400:
        return {}
    out: dict[str, dict] = {}
    for g in res.json():
        sid = g.get("submissionId") or g.get("submission_id")
        if sid:
            out[str(sid)] = g
    return out


async def _enrich_submission(
    submission: Submission, headers: dict[str, str]
) -> SubmissionResponse:
    ids = [str(f.file_ref_id) for f in submission.files]
    file_meta = await _fetch_file_meta_batch(ids, headers)
    grade_by_sub = await _fetch_grades_batch([str(submission.id)], headers)
    return _build_response(submission, file_meta, grade_by_sub)


def _build_response(
    submission: Submission,
    file_meta: dict[str, dict],
    grade_by_sub: dict[str, dict] | None = None,
) -> SubmissionResponse:
    files: list[FileRefResponse] = []
    for f in submission.files:
        meta = file_meta.get(str(f.file_ref_id), {})
        files.append(
            FileRefResponse(
                file_ref_id=f.file_ref_id,
                id=f.id,
                name=meta.get("name") or f.name,
                size_bytes=meta.get("sizeBytes"),
                content_type=meta.get("contentType"),
                url=meta.get("url"),
            )
        )
    grade_payload = (grade_by_sub or {}).get(str(submission.id))
    grade_obj = (
        GradeInline.model_validate(grade_payload) if grade_payload else None
    )
    return SubmissionResponse(
        id=submission.id,
        assignment_id=submission.assignment_id,
        student_id=submission.student_id,
        student_name=submission.student_name,
        submitted_at=submission.submitted_at,
        status=submission.status,
        files=files,
        grade=grade_obj,
    )
