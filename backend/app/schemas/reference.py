"""Request/response shapes for the reference-data endpoints (PRD T5, T6):
`GET /subjects`, `GET /universities`, `GET /programs`, `GET /programs/{code}`.
"""

from pydantic import BaseModel


class SubjectPublic(BaseModel):
    code: str
    name_ms: str
    name_en: str
    group: str
    old_syllabus: bool

    model_config = {"from_attributes": True}


class UniversityPublic(BaseModel):
    code: str
    name: str

    model_config = {"from_attributes": True}


class RequirementPublic(BaseModel):
    """One category's (A or B) rule tree, kept alongside the original Malay
    text for the program detail page (PRD T6: "the original Malay rule text
    and source credit")."""

    category: str
    rules: dict
    text_ms: str
    unparsed: bool


class ProgramSummary(BaseModel):
    code: str
    name: str
    university_code: str
    university_name: str
    nec_code: str | None
    nec_name: str | None
    area: str | None
    level: str | None
    mode: str | None
    duration_value: int | None
    duration_unit: str | None
    avg_merit: float | None
    stem: bool
    tvet: bool
    bumiputera_only: bool
    interview: bool
    campuses: list[str]


class ProgramDetail(ProgramSummary):
    career_paths: list[str]
    requirements: list[RequirementPublic]
    general_requirements: list[RequirementPublic]
    source_credit: str
