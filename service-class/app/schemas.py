from pydantic import BaseModel, computed_field, Field, model_validator
from typing import Optional, Literal, Any
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
    professorId: UUID = Field(alias="professor_id")
    professorName: str = Field(alias="professor_name")
    term: ClassTerm
    studentCount: int = Field(default=0, alias="student_count")
    assignmentCount: int = Field(default=0, alias="assignment_count")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "by_alias": True
    }

    @model_validator(mode="before")
    @classmethod
    def assemble_term(cls, data: Any) -> Any:
        if hasattr(data, "__dict__"):
            return {
                "id": data.id,
                "code": data.code,
                "name": data.name,
                "description": data.description,
                "professor_id": data.professor_id,   
                "professor_name": data.professor_name, 
                "student_count": 0, 
                "assignment_count": 0, 
                "term": {
                    "season": data.term_season,
                    "year": data.term_year,
                    "startsOn": data.term_starts_on,
                    "endsOn": data.term_ends_on,
                }
            }
        return data