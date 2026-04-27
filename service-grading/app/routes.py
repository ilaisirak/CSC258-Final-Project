# Defines the HTTP endpoints for the grading service.
# All routes are async and use the get_db dependency for database access.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Grade
from app.schemas import GradeUpsert, GradeResponse, GradeUpdate

router = APIRouter()

# Create or update a grade for a submission (professor).
# Uses an upsert pattern — if a grade already exists for the given
# submission_id it is updated in place, otherwise a new one is created.
# This prevents duplicate grades from being created if a professor
# submits the grading form more than once.
@router.post("/grading", response_model=GradeResponse)
async def upsert_grade(payload: GradeUpsert, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(Grade).where(Grade.submission_id == payload.submissionId)
    )
    grade = existing.scalar_one_or_none()

    if grade:
        grade.score           = payload.score
        grade.points_possible = payload.pointsPossible
        grade.feedback        = payload.feedback
        grade.graded_by_id    = payload.gradedById
    else:
        grade = Grade(
            submission_id   = payload.submissionId,
            score           = payload.score,
            points_possible = payload.pointsPossible,
            feedback        = payload.feedback,
            graded_by_id    = payload.gradedById,
        )
        db.add(grade)

    await db.commit()
    await db.refresh(grade)
    return grade

# Retrieve a single grade by its UUID.
# Returns 404 if no grade with the given ID exists.
@router.get("/grading/{grade_id}", response_model=GradeResponse)
async def get_grade(grade_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Grade).where(Grade.id == grade_id))
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    return grade

# Retrieve all grades, optionally filtered by studentId.
# Note: the Grade model does not store student_id directly — this filter
# requires a join through the submission service and is not yet implemented.
@router.get("/grading", response_model=list[GradeResponse])
async def get_grades(studentId: str = None, db: AsyncSession = Depends(get_db)):
    query = select(Grade)
    if studentId:
        query = query.where(Grade.student_id == studentId)
    result = await db.execute(query)
    return result.scalars().all()

# Update the score and feedback of an existing grade (professor).
# Only score and feedback can be changed — submission and grader
# references are immutable after creation.
# Returns 404 if the grade does not exist.
@router.patch("/grading/{grade_id}", response_model=GradeResponse)
async def update_grade(grade_id: str, payload: GradeUpdate, db: AsyncSession = Depends(get_db)):
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