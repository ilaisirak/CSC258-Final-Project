from pydantic import BaseModel, computed_field
from typing import Optional, Literal
from uuid import UUID

TermSeason = Literal["spring", "fall", "winter", "summer"]

class ClassTerm(BaseModel):
    season: TermSeason
    year: int
    startsOn: str
    endsOn: str

    @computed_field
    @property
    def label(self) -> str:
        return f"{self.season.capitalize()} {self.year}"


class ClassCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    professorId: UUID
    professorName: str
    term: ClassTerm


class ClassResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str]
    professorId: UUID
    professorName: str
    term: ClassTerm
    studentCount: int = 0
    assignmentCount: int = 0

    model_config = {"from_attributes": True}