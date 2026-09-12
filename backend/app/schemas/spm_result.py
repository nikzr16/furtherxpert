"""Request/response shapes for `GET/PUT /me/results` (PRD T1, T6).

Grade format is validated here (a fixed, static list -- no DB lookup
needed); whether the subject code itself exists, and whether BM/Sejarah are
present, are business rules checked in `app/services/results.py` against the
DB (see that module's docstring).
"""

from pydantic import BaseModel, field_validator

from app.models.spm_result import SPM_GRADES


class SPMResultIn(BaseModel):
    subject_code: str
    grade: str

    @field_validator("grade")
    @classmethod
    def _grade_must_be_known(cls, value: str) -> str:
        if value not in SPM_GRADES:
            raise ValueError(f"grade must be one of {', '.join(SPM_GRADES)}")
        return value


class SPMResultOut(BaseModel):
    subject_code: str
    subject_name_ms: str
    subject_name_en: str
    grade: str
