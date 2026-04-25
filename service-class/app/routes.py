from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Class
from app.schemas import ClassResponse, ClassCreate

router = APIRouter()

# Create a new class (professor)
@router.post("/class", response_model=ClassResponse)
async def create_class(payload: ClassCreate, db: AsyncSession = Depends(get_db)):
    class_ = Class(**payload.model_dump())
    db.add(class_)
    await db.commit()
    await db.refresh(class_)
    return class_

# Get a single class by id
@router.get("/class/{class_id}", response_model=ClassResponse)
async def get_class(class_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Class).where(Class.id == class_id)
    )
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")
    return class_

# Get all classes
@router.get("/classes", response_model=list[ClassResponse])
async def get_classes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Class))
    return result.scalars().all()