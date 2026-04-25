from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Class
from app.schemas import ClassCreate, ClassResponse

router = APIRouter()

@router.post("/classes", response_model=ClassResponse)
async def create_class(payload: ClassCreate, db: AsyncSession = Depends(get_db)):
    class_ = Class(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        professor_id=payload.professorId,
        professor_name=payload.professorName,
        term_season=payload.term.season,
        term_year=payload.term.year,
        term_starts_on=payload.term.startsOn,
        term_ends_on=payload.term.endsOn,
    )
    db.add(class_)
    await db.commit()
    await db.refresh(class_)
    return class_

@router.get("/classes", response_model=list[ClassResponse])
async def get_classes(professor_id: str = None, student_id: str = None, db: AsyncSession = Depends(get_db)):
    query = select(Class)
    if professor_id:
        query = query.where(Class.professor_id == professor_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/classes/{class_id}", response_model=ClassResponse)
async def get_class(class_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Class).where(Class.id == class_id))
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")
    return class_

@router.get("/classes/{class_id}/roster", response_model=list)
async def get_roster(class_id: str, db: AsyncSession = Depends(get_db)):
    # Placeholder — requires enrollment table or call to user service
    return []

@router.post("/classes/{class_id}/roster")
async def add_student(class_id: str, db: AsyncSession = Depends(get_db)):
    # Placeholder — requires enrollment table or call to user service
    return {}

@router.delete("/classes/{class_id}/roster/{user_id}")
async def remove_student(class_id: str, user_id: str, db: AsyncSession = Depends(get_db)):
    # Placeholder — requires enrollment table or call to user service
    return {}