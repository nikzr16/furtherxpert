"""SPM results (`spm_results`): read and upsert (PRD T1, T2, T6; plan Phase 4
tasks 2 and 4).

`upsert_results` inserts-or-updates each subject/grade row in the payload
(PRD T6: "upserts SPM grades") -- it never deletes a previously saved
subject the payload happens to omit. Every payload must still include
Bahasa Melayu (`BM`) and Sejarah (`SJ`, `app/importer/subjects.py`): the
plan's Check gates syarat am (PRD T2) on those two subjects always being on
file. Grade format is validated in `app/schemas/spm_result.py`; this module
validates subject codes against the DB (unknown codes are a 400, PRD T6/T2).
"""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DbSession

from app.models.analysis import Analysis
from app.models.spm_result import SPMResult
from app.models.subject import Subject
from app.schemas.spm_result import SPMResultIn

# Bahasa Melayu, Sejarah (app/importer/subjects.py) -- syarat am requires at
# least C in BM and E in Sejarah (PRD T2); every save must include both so
# eligibility (Phase 5) always has them to check.
REQUIRED_SUBJECT_CODES = ("BM", "SJ")


class DuplicateSubjectError(Exception):
    def __init__(self, codes: set[str]) -> None:
        self.codes = sorted(codes)
        super().__init__(f"Duplicate subject code(s) in payload: {', '.join(self.codes)}")


class MissingRequiredSubjectsError(Exception):
    def __init__(self, codes: set[str]) -> None:
        self.codes = sorted(codes)
        super().__init__(f"Missing required subject(s): {', '.join(self.codes)}")


class UnknownSubjectError(Exception):
    def __init__(self, codes: set[str]) -> None:
        self.codes = sorted(codes)
        super().__init__(f"Unknown subject code(s): {', '.join(self.codes)}")


def _serialize(result: SPMResult, subject: Subject) -> dict:
    return {
        "subject_code": subject.code,
        "subject_name_ms": subject.name_ms,
        "subject_name_en": subject.name_en,
        "grade": result.grade,
    }


def list_results(db: DbSession, user_id: uuid.UUID) -> list[dict]:
    rows = db.execute(
        select(SPMResult, Subject)
        .join(Subject, SPMResult.subject_id == Subject.id)
        .where(SPMResult.user_id == user_id)
        .order_by(Subject.name_ms)
    ).all()
    return [_serialize(result, subject) for result, subject in rows]


def upsert_results(db: DbSession, user_id: uuid.UUID, items: list[SPMResultIn]) -> list[dict]:
    codes = [item.subject_code for item in items]
    seen: set[str] = set()
    duplicates = {code for code in codes if code in seen or seen.add(code)}  # type: ignore[func-returns-value]
    if duplicates:
        raise DuplicateSubjectError(duplicates)

    code_set = set(codes)
    missing_required = set(REQUIRED_SUBJECT_CODES) - code_set
    if missing_required:
        raise MissingRequiredSubjectsError(missing_required)

    subjects = {row.code: row for row in db.execute(select(Subject).where(Subject.code.in_(code_set))).scalars()}
    unknown = code_set - subjects.keys()
    if unknown:
        raise UnknownSubjectError(unknown)

    existing = {
        row.subject_id: row
        for row in db.execute(select(SPMResult).where(SPMResult.user_id == user_id)).scalars()
    }
    for item in items:
        subject = subjects[item.subject_code]
        row = existing.get(subject.id)
        if row is None:
            db.add(SPMResult(user_id=user_id, subject_id=subject.id, grade=item.grade))
        else:
            row.grade = item.grade

    # Invalidate the cached analysis (Phase 5): a changed result set means
    # the cached scores/Best Fit are stale, so the next `GET /me/analysis`
    # must recompute (PRD T5).
    db.execute(delete(Analysis).where(Analysis.user_id == user_id))
    db.commit()

    return list_results(db, user_id)
