# Defines the HTTP endpoints for the grading service.
# All routes are async and use the get_db dependency for database access.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Grade
from app.schemas import GradeUpsert, GradeResponse, GradeUpdate
from app.auth import (
    CurrentUser,
    get_auth_header,
    get_current_user,
    require_role,
)
from app.peer import SUBMISSION_SERVICE_URL, mtls_client

router = APIRouter()

# Create or update a grade for a submission (professor).
# Uses an upsert pattern — if a grade already exists for the given
# submission_id it is updated in place, otherwise a new one is created.
@router.post("/grading", response_model=GradeResponse)
async def upsert_grade(
    payload: GradeUpsert,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role("professor")),
):
    # graded_by_id is always the gateway-verified caller.
    grader_id = user.id
    existing = await db.execute(
        select(Grade).where(Grade.submission_id == payload.submissionId)
    )
    grade = existing.scalar_one_or_none()

    if grade:
        grade.score           = payload.score
        grade.points_possible = payload.pointsPossible
        grade.feedback        = payload.feedback
        grade.graded_by_id    = grader_id
    else:
        grade = Grade(
            submission_id   = payload.submissionId,
            score           = payload.score,
            points_possible = payload.pointsPossible,
            feedback        = payload.feedback,
            graded_by_id    = grader_id,
        )
        db.add(grade)

    await db.commit()
    await db.refresh(grade)
    return grade


# Retrieve a single grade by its UUID.
@router.get("/grading/{grade_id}", response_model=GradeResponse)
async def get_grade(
    grade_id: str,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(select(Grade).where(Grade.id == grade_id))
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    return grade


# Retrieve all grades, optionally filtered.
#  - studentId:      resolves the student's submissions via service-submission,
#                    then returns grades for those submission ids.
#  - submissionIds:  comma-separated list of submission ids to look up
#                    directly (used by service-bff to batch grading reads).
@router.get("/grading", response_model=list[GradeResponse])
async def get_grades(
    studentId: str = None,
    submissionIds: str = None,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
    auth_header: dict = Depends(get_auth_header),
):
    if submissionIds:
        ids = [s for s in submissionIds.split(",") if s]
        if not ids:
            return []
        result = await db.execute(
            select(Grade).where(Grade.submission_id.in_(ids))
        )
        return result.scalars().all()

    if studentId:
        async with mtls_client() as client:
            response = await client.get(
                f"{SUBMISSION_SERVICE_URL}/submissions",
                params={"studentId": studentId},
                headers=auth_header,
            )
            response.raise_for_status()
            submissions = response.json()
        submission_ids = [s["id"] for s in submissions]
        if not submission_ids:
            return []
        query = select(Grade).where(Grade.submission_id.in_(submission_ids))
    else:
        query = select(Grade)
    result = await db.execute(query)
    return result.scalars().all()


# Update the score and feedback of an existing grade (professor).
@router.patch("/grading/{grade_id}", response_model=GradeResponse)
async def update_grade(
    grade_id: str,
    payload: GradeUpdate,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_role("professor")),
):
    result = await db.execute(select(Grade).where(Grade.id == grade_id))
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    grade.score = payload.score
    if payload.feedback is not None:
        grade.feedback = payload.feedback
    await db.commit()
    await db.refresh(grade)
    return grade
