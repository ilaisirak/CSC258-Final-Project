from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EnrollmentResponse(BaseModel):
    id: UUID
    classId: UUID = Field(alias="class_id")
    studentId: UUID = Field(alias="student_id")
    enrolledAt: datetime = Field(alias="enrolled_at")

    model_config = {"from_attributes": True, "populate_by_name": True}


class AddStudentRequest(BaseModel):
    email: str


class EnrollmentCount(BaseModel):
    classId: UUID
    count: int


class StudentClassIds(BaseModel):
    studentId: UUID
    classIds: list[UUID]
