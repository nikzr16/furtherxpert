"""Reference-data endpoints (PRD T5, T6): `GET /subjects`, `GET /universities`,
`GET /programs`, `GET /programs/{code}`. Public -- no auth required, these are
form/filter/explore lists, not student data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.reference import ProgramDetail, ProgramSummary, SubjectPublic, UniversityPublic
from app.services import reference as reference_service

router = APIRouter(tags=["reference"])


@router.get("/subjects", response_model=list[SubjectPublic])
def read_subjects(db: Session = Depends(get_db)) -> list[dict]:
    return reference_service.list_subjects(db)


@router.get("/universities", response_model=list[UniversityPublic])
def read_universities(db: Session = Depends(get_db)) -> list:
    return reference_service.list_universities(db)


@router.get("/programs", response_model=list[ProgramSummary])
def read_programs(
    area: str | None = Query(default=None, description="Interest area name, e.g. 'Science & Technology'"),
    university: str | None = Query(default=None, description="University code, e.g. 'UE'"),
    q: str | None = Query(default=None, description="Case-insensitive text search on program name"),
    db: Session = Depends(get_db),
) -> list[dict]:
    try:
        return reference_service.list_programs(db, area=area, university=university, q=q)
    except reference_service.NoReferenceDataError:
        return []


@router.get("/programs/{code}", response_model=ProgramDetail)
def read_program(code: str, db: Session = Depends(get_db)) -> dict:
    try:
        return reference_service.get_program(db, code)
    except (reference_service.ProgramNotFoundError, reference_service.NoReferenceDataError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found") from exc
