# Defines the HTTP endpoints for the class service.
# Roster endpoints call the user service to resolve student data.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database import get_db
from app.models import Class, Enrollment
from app.schemas import ClassCreate, ClassResponse, AddStudentRequest
import httpx

router = APIRouter()

# User service URL — resolved via docker-compose service name
USER_SERVICE_URL = "http://service-user:8000"


# Create a new class (professor).
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


@router.get("/classes/{class_id}", response_model=ClassResponse)
async def get_class(class_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Class).where(Class.id == class_id))
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")
    return class_


# Retrieve all classes, optionally filtered by professor_id.
@router.get("/classes", response_model=list[ClassResponse])
async def get_classes(
    professorId: str = None,
    studentId: str = None,
    professor_id: str = None,
    student_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    resolved_professor = professorId or professor_id
    resolved_student = studentId or student_id

    query = select(Class)
    if resolved_professor:
        query = query.where(Class.professor_id == resolved_professor)
    if resolved_student:
        enrollment_result = await db.execute(
            select(Enrollment.class_id).where(Enrollment.student_id == resolved_student)
        )
        class_ids = [row[0] for row in enrollment_result.fetchall()]
        query = query.where(Class.id.in_(class_ids))
    result = await db.execute(query)
    classes = result.scalars().all()
    return classes

# Get all students enrolled in a class.
# Fetches enrollment records then calls the user service to resolve
# each student_id into a full user object.
@router.get("/classes/{class_id}/roster")
async def get_roster(class_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Enrollment).where(Enrollment.class_id == class_id)
    )
    enrollments = result.scalars().all()

    if not enrollments:
        return []

    # Call user service to resolve each student UUID to a user object
    students = []
    async with httpx.AsyncClient() as client:
        for enrollment in enrollments:
            try:
                response = await client.get(
                    f"{USER_SERVICE_URL}/users/{enrollment.student_id}"
                )
                if response.status_code == 200:
                    students.append(response.json())
            except httpx.RequestError:
                # If user service is unavailable, return what we have
                continue

    return students

@router.post("/classes/{class_id}/roster/{student_id}")
async def add_student(class_id: str, student_id: str, db: AsyncSession = Depends(get_db)):
    # Verify class exists
    class_result = await db.execute(select(Class).where(Class.id == class_id))
    if not class_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Class not found")

    # Check not already enrolled
    existing = await db.execute(
        select(Enrollment).where(
            Enrollment.class_id == class_id,
            Enrollment.student_id == student_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Student already enrolled")

    enrollment = Enrollment(
        class_id=class_id,
        student_id=student_id
    )
    db.add(enrollment)
    await db.commit()

    return {"message": "Student enrolled", "studentId": student_id, "classId": class_id}

# Remove a student from a class.
@router.delete("/classes/{class_id}/roster/{user_id}")
async def remove_student(class_id: str, user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.class_id == class_id,
            Enrollment.student_id == user_id
        )
    )
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    await db.execute(
        delete(Enrollment).where(
            Enrollment.class_id == class_id,
            Enrollment.student_id == user_id
        )
    )
    await db.commit()
    return {"message": "Student removed"}