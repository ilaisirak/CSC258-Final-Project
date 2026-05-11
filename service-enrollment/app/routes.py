# Roster / enrollment endpoints.
#
# This service owns the enrollments table and is the sole writer.
# All callers (gateway, BFF, peer services) talk to this service
# directly; service-class does not proxy through.

from typing import Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    CurrentUser,
    get_auth_header,
    get_current_user,
    require_role,
)
from app.database import get_db
from app.models import Enrollment
from app.peer import CLASS_SERVICE_URL, USER_SERVICE_URL, mtls_client
from app.schemas import AddStudentRequest, EnrollmentResponse

router = APIRouter()


async def _verify_class_exists(class_id: str, auth_header: dict) -> None:
    """Peer-call service-class to confirm the class id is real.

    404s the request if the class doesn't exist. Network failures
    surface as 502 so the caller can distinguish "class doesn't exist"
    from "class service is down".
    """
    async with mtls_client(timeout=5.0) as client:
        try:
            res = await client.get(
                f"{CLASS_SERVICE_URL}/classes/{class_id}",
                headers=auth_header,
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502, detail=f"Class service unreachable: {exc}"
            )
    if res.status_code == 404:
        raise HTTPException(status_code=404, detail="Class not found")
    if res.status_code >= 400:
        raise HTTPException(
            status_code=502, detail=f"Class service error: {res.text}"
        )


# ───────────────── roster (used by gateway public routes) ──────


@router.get("/classes/{class_id}/roster")
async def get_roster(
    class_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
    auth_header: dict = Depends(get_auth_header),
):
    """Return full student records for everyone enrolled in a class."""
    enrollments = (
        await db.execute(
            select(Enrollment).where(Enrollment.class_id == class_id)
        )
    ).scalars().all()
    if not enrollments:
        return []

    students: list[dict] = []
    async with mtls_client() as client:
        for e in enrollments:
            try:
                res = await client.get(
                    f"{USER_SERVICE_URL}/users/by-id/{e.student_id}",
                    headers=auth_header,
                )
                if res.status_code == 200:
                    students.append(res.json())
            except httpx.RequestError:
                continue
    return students


@router.post("/classes/{class_id}/roster/by-email")
async def add_student_by_email(
    class_id: UUID,
    payload: AddStudentRequest,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_role("professor")),
    auth_header: dict = Depends(get_auth_header),
):
    await _verify_class_exists(str(class_id), auth_header)

    async with mtls_client() as client:
        try:
            res = await client.get(
                f"{USER_SERVICE_URL}/users/search",
                params={"email": payload.email},
                headers=auth_header,
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502, detail=f"User service unreachable: {exc}"
            )
    if res.status_code != 200:
        raise HTTPException(status_code=502, detail="User service error")
    matches = res.json()
    if not matches:
        raise HTTPException(status_code=404, detail="No user with that email")
    user = matches[0]
    if user.get("role") != "student":
        raise HTTPException(status_code=400, detail="User is not a student")
    return await _enroll(class_id, UUID(str(user["id"])), db)


@router.post("/classes/{class_id}/roster/{student_id}")
async def add_student(
    class_id: UUID,
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_role("professor")),
    auth_header: dict = Depends(get_auth_header),
):
    await _verify_class_exists(str(class_id), auth_header)
    return await _enroll(class_id, student_id, db)


@router.delete("/classes/{class_id}/roster/{user_id}")
async def remove_student(
    class_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_role("professor")),
):
    row = (
        await db.execute(
            select(Enrollment).where(
                Enrollment.class_id == class_id,
                Enrollment.student_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    await db.execute(
        delete(Enrollment).where(
            Enrollment.class_id == class_id,
            Enrollment.student_id == user_id,
        )
    )
    await db.commit()
    return {"message": "Student removed"}


# ───────────────── internal endpoints (peer-called by service-class) ──


@router.get("/enrollments", response_model=list[EnrollmentResponse])
async def list_enrollments(
    classId: Optional[UUID] = None,
    studentId: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    """Filterable enrollment listing.

    service-class peer-calls this with `studentId=` to filter its class
    listing, and with `classId=` to compute student counts.
    """
    query = select(Enrollment)
    if classId is not None:
        query = query.where(Enrollment.class_id == classId)
    if studentId is not None:
        query = query.where(Enrollment.student_id == studentId)
    rows = (await db.execute(query)).scalars().all()
    return rows


@router.get("/enrollments/count")
async def count_enrollments(
    classId: UUID,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    """Student count for one class. Cheap (single COUNT query)."""
    cnt = (
        await db.execute(
            select(func.count(Enrollment.id)).where(
                Enrollment.class_id == classId
            )
        )
    ).scalar() or 0
    return {"classId": str(classId), "count": cnt}


@router.get("/enrollments/counts")
async def count_enrollments_batch(
    classIds: str,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    """Batch student counts. classIds=comma,separated,uuids."""
    try:
        ids = [UUID(s) for s in classIds.split(",") if s]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid classIds")
    if not ids:
        return {}
    rows = (
        await db.execute(
            select(Enrollment.class_id, func.count(Enrollment.id))
            .where(Enrollment.class_id.in_(ids))
            .group_by(Enrollment.class_id)
        )
    ).all()
    counts = {str(cid): cnt for cid, cnt in rows}
    # Zero-fill missing
    return {str(i): counts.get(str(i), 0) for i in ids}


# ───────────────── shared helper ────────────────


async def _enroll(class_id: UUID, student_id: UUID, db: AsyncSession):
    dup = (
        await db.execute(
            select(Enrollment).where(
                Enrollment.class_id == class_id,
                Enrollment.student_id == student_id,
            )
        )
    ).scalar_one_or_none()
    if dup:
        raise HTTPException(status_code=409, detail="Student already enrolled")
    row = Enrollment(class_id=class_id, student_id=student_id)
    db.add(row)
    await db.commit()
    return {
        "message": "Student enrolled",
        "studentId": str(student_id),
        "classId": str(class_id),
    }
