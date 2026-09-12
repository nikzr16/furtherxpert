"""Reference-data reads: subjects, universities, programs (PRD T5, T6).

Pure read layer on top of a `Session` -- the API layer (`app/api/reference.py`)
only translates HTTP <-> these calls. "Current session" is always the most
recently loaded one (`sessions.created_at` desc): the yearly data migration
replaces a session's rows in place, and a brand new session row only appears
when a new year's snapshot is loaded (plan Phase 3 task 5).
"""

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession, joinedload

from app.importer.reference_data import match_interest_area
from app.models.program import Program
from app.models.requirement import GeneralRequirement, ProgramRequirement
from app.models.session import Session as UpuSession
from app.models.subject import Subject, SubjectGroup
from app.models.university import University


class ProgramNotFoundError(Exception):
    """Raised when no program with the given code exists in the current session."""


class NoReferenceDataError(Exception):
    """Raised when no session has been loaded yet (empty reference data)."""


def list_subjects(db: DbSession) -> list[dict]:
    rows = db.execute(
        select(Subject, SubjectGroup.code.label("group_code"))
        .join(SubjectGroup, Subject.group_id == SubjectGroup.id)
        .order_by(Subject.name_ms)
    ).all()
    return [
        {
            "code": subject.code,
            "name_ms": subject.name_ms,
            "name_en": subject.name_en,
            "group": group_code,
            "old_syllabus": subject.old_syllabus,
        }
        for subject, group_code in rows
    ]


def list_universities(db: DbSession) -> list[University]:
    return list(db.execute(select(University).order_by(University.name)).scalars())


def _current_session(db: DbSession) -> UpuSession:
    session = db.execute(select(UpuSession).order_by(UpuSession.created_at.desc()).limit(1)).scalar_one_or_none()
    if session is None:
        raise NoReferenceDataError("No UPU reference session has been loaded yet")
    return session


def _program_summary(program: Program, university: University) -> dict:
    return {
        "code": program.code,
        "name": program.name,
        "university_code": university.code,
        "university_name": university.name,
        "nec_code": program.nec_code,
        "nec_name": program.nec_name,
        "area": match_interest_area(program.nec_code),
        "level": program.level,
        "mode": program.mode,
        "duration_value": program.duration_value,
        "duration_unit": program.duration_unit,
        "avg_merit": program.avg_merit,
        "stem": program.stem,
        "tvet": program.tvet,
        "bumiputera_only": program.bumiputera_only,
        "interview": program.interview,
        "campuses": [c.name for c in program.campuses],
    }


def list_programs(
    db: DbSession,
    *,
    area: str | None = None,
    university: str | None = None,
    q: str | None = None,
) -> list[dict]:
    session = _current_session(db)

    stmt = (
        select(Program, University)
        .join(University, Program.university_id == University.id)
        .options(joinedload(Program.campuses))
        .where(Program.session_id == session.id)
        .order_by(Program.name)
    )
    if university:
        stmt = stmt.where(University.code == university.upper())
    if q:
        stmt = stmt.where(Program.name.ilike(f"%{q}%"))

    rows = db.execute(stmt).unique().all()
    summaries = [_program_summary(program, uni) for program, uni in rows]
    if area:
        summaries = [s for s in summaries if s["area"] == area]
    return summaries


def get_program(db: DbSession, code: str) -> dict:
    session = _current_session(db)

    row = db.execute(
        select(Program, University)
        .join(University, Program.university_id == University.id)
        .options(joinedload(Program.campuses))
        .where(Program.session_id == session.id, Program.code == code)
    ).unique().one_or_none()
    if row is None:
        raise ProgramNotFoundError(code)
    program, university = row

    requirements = list(
        db.execute(
            select(ProgramRequirement)
            .where(ProgramRequirement.program_id == program.id)
            .order_by(ProgramRequirement.category)
        ).scalars()
    )
    general_requirements = list(
        db.execute(
            select(GeneralRequirement)
            .where(GeneralRequirement.session_id == session.id)
            .order_by(GeneralRequirement.category)
        ).scalars()
    )

    summary = _program_summary(program, university)
    summary["career_paths"] = program.career_paths
    summary["requirements"] = [
        {"category": r.category, "rules": r.rules, "text_ms": r.text_ms, "unparsed": r.unparsed}
        for r in requirements
    ]
    summary["general_requirements"] = [
        {"category": r.category, "rules": r.rules, "text_ms": r.text_ms, "unparsed": r.unparsed}
        for r in general_requirements
    ]
    # PRD T5: "The website credits the source: 'Source: e-Panduan UPU, KPT,
    # sesi 2026/2027'".
    summary["source_credit"] = f"Source: e-Panduan UPU, KPT, sesi {session.name}"
    return summary
