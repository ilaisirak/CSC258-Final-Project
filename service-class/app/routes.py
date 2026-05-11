# HTTP endpoints for the class service.
#
# This module is pure CRUD over the class catalog.
# Roster lives in service-enrollment; student/assignment count
# enrichment and the studentId filter (which requires a peer call
# to enrollment) live in service-bff (/views/classes).

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    CurrentUser,
    get_current_user,
    require_role,
)
from app.database import get_db
from app.models import Class
from app.schemas import ClassCreate, ClassResponse

router = APIRouter()


def _attach_defaults(class_: Class) -> Class:
    # ClassResponse declares non-nullable counts; service-class no
    # longer enriches them, so default to 0 for every row coming out.
    class_.student_count = 0
    class_.assignment_count = 0
    return class_


@router.post("/classes", response_model=ClassResponse)
async def create_class(
    payload: ClassCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role("professor")),
):
    # Always trust the gateway-verified identity, never the request body,
    # for the professor binding. Without this the SPA could post any
    # professorId and have it accepted.
    class_ = Class(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        professor_id=user.id,
        professor_name=user.name or "",
        term_season=payload.term.season,
        term_year=payload.term.year,
        term_starts_on=payload.term.startsOn,
        term_ends_on=payload.term.endsOn,
    )
    db.add(class_)
    await db.commit()
    await db.refresh(class_)
    return _attach_defaults(class_)


@router.get("/classes/{class_id}", response_model=ClassResponse)
async def get_class(
    class_id: str,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(select(Class).where(Class.id == class_id))
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")
    return _attach_defaults(class_)


@router.get("/classes", response_model=list[ClassResponse])
async def get_classes(
    professorId: Optional[str] = None,
    professor_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    resolved_professor = professorId or professor_id

    query = select(Class)
    if resolved_professor:
        query = query.where(Class.professor_id == resolved_professor)

    classes = (await db.execute(query)).scalars().all()
    return [_attach_defaults(c) for c in classes]
