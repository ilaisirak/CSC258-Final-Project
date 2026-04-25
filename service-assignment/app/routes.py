from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Assignment
from app.schemas import AssignmentCreate, AssignmentResponse

router = APIRouter()

@router.post("/assignments", response_model=AssignmentResponse)
async def create_assignment(payload: AssignmentCreate, db: AsyncSession = Depends(get_db)):
    assignment = Assignment(
        class_id=payload.classId,
        title=payload.title,
        description=payload.description,
        due_at=payload.dueAt,
        points_possible=payload.pointsPossible,
        status=payload.status,
        allow_resubmission=payload.allowResubmission,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment

@router.get("/assignments/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(assignment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment

@router.get("/assignments", response_model=list[AssignmentResponse])
async def get_assignments(classId: str = None, studentId: str = None, db: AsyncSession = Depends(get_db)):
    query = select(Assignment)
    if classId:
        query = query.where(Assignment.class_id == classId)
    result = await db.execute(query)
    return result.scalars().all()

@router.patch("/assignments/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(assignment_id: str, payload: AssignmentCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignment.title = payload.title
    assignment.description = payload.description
    assignment.due_at = payload.dueAt
    assignment.points_possible = payload.pointsPossible
    assignment.status = payload.status
    assignment.allow_resubmission = payload.allowResubmission
    await db.commit()
    await db.refresh(assignment)
    return assignment