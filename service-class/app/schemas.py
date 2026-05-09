# Pydantic models used for request validation and response serialization.
# Field names use camelCase to match the frontend API contract.
# Aliases map camelCase fields to the snake_case column names in the ORM model.

from datetime import datetime
from pydantic import BaseModel, computed_field, Field, model_validator
from typing import Optional, Literal, Any
from uuid import UUID

# Valid academic term seasons.
TermSeason = Literal["spring", "fall", "winter", "summer"]

# Represents the term nested object used in both requests and responses.
# The label field is computed from season and year and never stored in
# the database — it is generated at serialization time.
class ClassTerm(BaseModel):
    season: TermSeason
    year: int
    startsOn: str
    endsOn: str

    @computed_field
    @property
    def label(self) -> str:
        return f"{self.season.capitalize()} {self.year}"

# Validates the request body for POST /classes.
# Field names are camelCase to match incoming JSON from the frontend.
class ClassCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    professorId: UUID
    professorName: str
    term: ClassTerm

    model_config = {"from_attributes": True, "populate_by_name": True}

# Shapes the response returned by all class endpoints.
# Field aliases map ORM snake_case column names to camelCase JSON output.
#
# Because the Class model stores term fields as flat columns (term_season,
# term_year, etc.), assemble_term reconstructs the nested ClassTerm object
# before Pydantic validates the response. This runs automatically whenever
# a Class ORM object is passed as a response.
#
# studentCount and assignmentCount are included with default 0; actual
# values will be attached to the ORM object before returning so that
# Pydantic can read them during serialisation.
class ClassResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    professorId: UUID = Field(alias="professor_id")
    professorName: str = Field(alias="professor_name")
    term: ClassTerm
    studentCount: int = 0
    assignmentCount: int = 0

    model_config = {"from_attributes": True, "populate_by_name": True}

    @model_validator(mode="before")
    @classmethod
    def assemble_term(cls, data: Any) -> Any:
        # When receiving an ORM object, convert it to a dict and
        # reconstruct the nested term object from flat column values.
        # Also read student_count and assignment_count if they were
        # temporarily set on the ORM object.
        if hasattr(data, "__dict__"):
            return {
                "id": data.id,
                "code": data.code,
                "name": data.name,
                "description": data.description,
                "professor_id": data.professor_id,
                "professor_name": data.professor_name,
                "student_count": getattr(data, "student_count", 0),
                "assignment_count": getattr(data, "assignment_count", 0),
                "term": {
                    "season": data.term_season,
                    "year": data.term_year,
                    "startsOn": data.term_starts_on,
                    "endsOn": data.term_ends_on,
                }
            }
        return data

# Represents a single enrollment record.
class EnrollmentResponse(BaseModel):
    id: UUID
    classId: UUID      = Field(alias="class_id")
    studentId: UUID    = Field(alias="student_id")
    enrolledAt: datetime = Field(alias="enrolled_at")

    model_config = {"from_attributes": True, "populate_by_name": True}

# Request body for adding a student to a class by email.
# The class service calls the user service to resolve the email to a UUID.
class AddStudentRequest(BaseModel):
    email: str