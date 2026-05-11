# Pydantic models used for request validation and response serialization.
# Field names use camelCase to match the frontend API contract.
# Aliases map camelCase fields to the snake_case column names in the ORM model.

from pydantic import BaseModel, Field, computed_field
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime, timezone

# Valid lifecycle states for an assignment.
AssignmentStatus = Literal["draft", "open", "closed"]

# Validates the request body for POST /assignments.
# Field names are camelCase to match incoming JSON from the frontend.
class AssignmentCreate(BaseModel):
    classId: UUID
    title: str
    description: str = ""
    dueAt: Optional[datetime] = None
    pointsPossible: float = 100.0
    status: AssignmentStatus = "open"
    allowResubmission: bool = True

    model_config = {"from_attributes": True, "populate_by_name": True}

# Shapes the response returned by all assignment endpoints.
# Field aliases map ORM snake_case column names to camelCase JSON output.
# isOpen and isOverdue are computed at serialization time from status and
# due_at so the frontend never needs to compare timestamps locally — the
# backend is the single source of truth for an assignment's availability.
class AssignmentResponse(BaseModel):
    id: UUID
    classId: UUID               = Field(alias="class_id")
    title: str
    description: str
    dueAt: Optional[datetime]   = Field(alias="due_at")
    pointsPossible: float       = Field(alias="points_possible")
    status: AssignmentStatus
    allowResubmission: bool     = Field(alias="allow_resubmission")

    model_config = {"from_attributes": True, "populate_by_name": True}

    @computed_field
    @property
    def isOpen(self) -> bool:
        # An assignment is open when its lifecycle state is "open" and the
        # due date (if any) has not passed.
        if self.status != "open":
            return False
        if self.dueAt is None:
            return True
        return _now_naive() <= _strip_tz(self.dueAt)

    @computed_field
    @property
    def isOverdue(self) -> bool:
        # Overdue means the due date is in the past. Status is irrelevant —
        # a closed-but-not-yet-due assignment is not overdue, but a
        # past-due open assignment is.
        if self.dueAt is None:
            return False
        return _now_naive() > _strip_tz(self.dueAt)


# Helpers that normalize the assignment due_at column (TIMESTAMP WITHOUT
# TIME ZONE) and current time to the same naive representation so they
# can be compared without raising.
def _now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _strip_tz(value: datetime) -> datetime:
    return value.replace(tzinfo=None) if value.tzinfo is not None else value


# Pre-assembled view of an assignment for a particular student, including
# the class display fields and the student's submission for that
# assignment if one exists. Returned by GET /assignments/for-student/{id}
# so the frontend does not need to fan out across services.
class AssignmentForStudentResponse(BaseModel):
    assignment: AssignmentResponse
    className: str
    classCode: str
    submission: Optional[dict] = None

    model_config = {"populate_by_name": True}