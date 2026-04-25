from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Assignment
from app.schemas import AssignmentCreate, AssignmentResponse

router = APIRouter()

# Create a new assignment (professor)
@router.post("/assignments", response_model=AssignmentResponse)
async def create_assignment(payload: AssignmentCreate, db: AsyncSession = Depends(get_db)):
    assignment = Assignment(**payload.model_dump())
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment

# Get all assignments for a class
@router.get("/assignments/class/{class_id}", response_model=list[AssignmentResponse])
async def get_assignments(class_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Assignment).where(Assignment.class_id == class_id)
    )
    return result.scalars().all()

# Get a single assignment by id
@router.get("/assignments/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment