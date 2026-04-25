from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Grade
from app.schemas import GradeUpsert, GradeResponse, GradeUpdate

router = APIRouter()

@router.post("/grading", response_model=GradeResponse)
async def upsert_grade(payload: GradeUpsert, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(Grade).where(Grade.submission_id == payload.submissionId)
    )
    grade = existing.scalar_one_or_none()

    if grade:
        grade.score = payload.score
        grade.points_possible = payload.pointsPossible
        grade.feedback = payload.feedback
        grade.graded_by_id = payload.gradedById
    else:
        grade = Grade(
            submission_id=payload.submissionId,
            score=payload.score,
            points_possible=payload.pointsPossible,
            feedback=payload.feedback,
            graded_by_id=payload.gradedById,
        )
        db.add(grade)

    await db.commit()
    await db.refresh(grade)
    return grade

@router.get("/grading/{grade_id}", response_model=GradeResponse)
async def get_grade(grade_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Grade).where(Grade.id == grade_id))
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    return grade

@router.get("/grading", response_model=list[GradeResponse])
async def get_grades(studentId: str = None, db: AsyncSession = Depends(get_db)):
    query = select(Grade)
    if studentId:
        query = query.where(Grade.student_id == studentId)
    result = await db.execute(query)
    return result.scalars().all()

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