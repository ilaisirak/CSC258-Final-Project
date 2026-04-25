from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Grade
from app.schemas import GradeUpsert, GradeResponse

router = APIRouter()

# Assign a grade (professor)
@router.post("/grades", response_model=GradeResponse)
async def create_grade(payload: GradeUpsert, db: AsyncSession = Depends(get_db)):
    # prevent duplicate grades for the same submission
    existing = await db.execute(
        select(Grade).where(Grade.submission_id == payload.submission_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Submission already graded")

    grade = Grade(**payload.model_dump())
    db.add(grade)
    await db.commit()
    await db.refresh(grade)
    return grade

# Get a single grade by id
@router.get("/grades/{grade_id}", response_model=GradeResponse)
async def get_grade(grade_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Grade).where(Grade.id == grade_id)
    )
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    return grade

# Get all grades for a specific student
@router.get("/grades/student/{student_id}", response_model=list[GradeResponse])
async def get_grades_by_student(student_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Grade).where(Grade.student_id == student_id)
    )
    return result.scalars().all()

# Get all grades for a specific assignment (professor view)
@router.get("/grades/assignment/{assignment_id}", response_model=list[GradeResponse])
async def get_grades_by_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Grade).where(Grade.assignment_id == assignment_id)
    )
    return result.scalars().all()

# Update a grade (professor)
@router.patch("/grades/{grade_id}", response_model=GradeResponse)
async def update_grade(grade_id: int, payload: GradeUpsert, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Grade).where(Grade.id == grade_id)
    )
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")

    grade.grade = payload.grade
    if payload.feedback is not None:
        grade.feedback = payload.feedback

    await db.commit()
    await db.refresh(grade)
    return grade