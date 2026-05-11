# Defines the HTTP endpoints for the assignment service.
# All routes are async and use the get_db dependency for database access.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Assignment
from app.schemas import (
    AssignmentCreate,
    AssignmentResponse,
)
from app.auth import (
    CurrentUser,
    get_current_user,
    require_role,
)

router = APIRouter()

# Create a new assignment for a given class (professor).
@router.post("/assignments", response_model=AssignmentResponse)
async def create_assignment(
    payload: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_role("professor")),
):
    assignment = Assignment(
        class_id=payload.classId,
        title=payload.title,
        description=payload.description,
        # Strip timezone info before storing — column is TIMESTAMP WITHOUT TIME ZONE
        due_at=payload.dueAt.replace(tzinfo=None) if payload.dueAt else None,
        points_possible=payload.pointsPossible,
        status=payload.status,
        allow_resubmission=payload.allowResubmission,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment

# Retrieve a single assignment by its UUID.
# Returns 404 if no assignment with the given ID exists.
@router.get("/assignments/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment

# Retrieve all assignments, optionally filtered by classId or studentId.
# classId filters assignments belonging to a specific class.
# studentId is accepted as a query param for interface compatibility
# but filtering by student requires submission data from another service.
@router.get("/assignments", response_model=list[AssignmentResponse])
async def get_assignments(
    classId: str = None,
    studentId: str = None,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    query = select(Assignment)
    if classId:
        query = query.where(Assignment.class_id == classId)
    result = await db.execute(query)
    return result.scalars().all()


# Pre-assembled view of all assignments visible to a student has moved
# to service-bff (see service-bff/app/routes.py:assignments_for_student).
# The gateway now routes /api/assignments/for-student/* to the BFF.

# Update an existing assignment's fields (professor).
# Returns 404 if the assignment does not exist.
@router.patch("/assignments/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: str,
    payload: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_role("professor")),
):
    result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignment.title              = payload.title
    assignment.description        = payload.description
    # Strip timezone info before storing — column is TIMESTAMP WITHOUT TIME ZONE
    assignment.due_at             = (
        payload.dueAt.replace(tzinfo=None) if payload.dueAt else None
    )
    assignment.points_possible    = payload.pointsPossible
    assignment.status             = payload.status
    assignment.allow_resubmission = payload.allowResubmission
    await db.commit()
    await db.refresh(assignment)
    return assignment