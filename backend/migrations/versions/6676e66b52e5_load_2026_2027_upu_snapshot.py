"""load 2026/2027 UPU snapshot

Revision ID: 6676e66b52e5
Revises: 57ab2a90bfa6
Create Date: 2026-09-12 12:00:00.000000

Phase 3 (PRD T5, T2; plan Phase 3 task 5): seeds the stable, non-session
reference tables (universities, subjects, subject_groups, interest_areas)
from the hand-written lists in `app/importer/reference_data.py` /
`app/importer/subjects.py` -- idempotent upserts, shared across every
session -- then loads `backend/data/upu/2026-2027.json` (written by
`app/importer/epanduan.py`) into the session-scoped tables (sessions,
programs, campuses, general_requirements, program_requirements).

Loading a session **replaces** all of that session's reference rows: any
existing programs/campuses/requirements for the same session name are
deleted before the snapshot's rows are inserted (PRD: "a new session fully
replaces the old one, including any admin edits"). Other sessions, and the
shared reference tables, are untouched.
"""
import json
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6676e66b52e5'
down_revision: Union[str, Sequence[str], None] = '57ab2a90bfa6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SNAPSHOT_PATH = Path(__file__).resolve().parents[2] / "data" / "upu" / "2026-2027.json"

# --- Lightweight table mirrors (data migrations should not import the ORM
# models, which can change shape after this revision is written) ---

subject_groups_t = sa.table(
    "subject_groups", sa.column("id", sa.Integer), sa.column("code", sa.String), sa.column("name", sa.String)
)
subjects_t = sa.table(
    "subjects",
    sa.column("id", sa.Integer),
    sa.column("code", sa.String),
    sa.column("name_ms", sa.String),
    sa.column("name_en", sa.String),
    sa.column("group_id", sa.Integer),
    sa.column("old_syllabus", sa.Boolean),
)
universities_t = sa.table(
    "universities", sa.column("id", sa.Integer), sa.column("code", sa.String), sa.column("name", sa.String)
)
interest_areas_t = sa.table(
    "interest_areas",
    sa.column("id", sa.Integer),
    sa.column("name", sa.String),
    sa.column("nec_prefixes", postgresql.JSONB),
    sa.column("exclude_nec_prefixes", postgresql.JSONB),
    sa.column("subject_groups", postgresql.JSONB),
)
sessions_t = sa.table(
    "sessions",
    sa.column("id", sa.Integer),
    sa.column("name", sa.String),
    sa.column("latest_spm_year", sa.Integer),
)
general_requirements_t = sa.table(
    "general_requirements",
    sa.column("id", sa.Integer),
    sa.column("session_id", sa.Integer),
    sa.column("category", sa.String),
    sa.column("rules", postgresql.JSONB),
    sa.column("text_ms", sa.Text),
    sa.column("unparsed", sa.Boolean),
)
programs_t = sa.table(
    "programs",
    sa.column("id", sa.Integer),
    sa.column("session_id", sa.Integer),
    sa.column("code", sa.String),
    sa.column("university_id", sa.Integer),
    sa.column("name", sa.String),
    sa.column("nec_code", sa.String),
    sa.column("nec_name", sa.String),
    sa.column("level", sa.String),
    sa.column("mode", sa.String),
    sa.column("duration_value", sa.Integer),
    sa.column("duration_unit", sa.String),
    sa.column("avg_merit", sa.Float),
    sa.column("stem", sa.Boolean),
    sa.column("tvet", sa.Boolean),
    sa.column("bumiputera_only", sa.Boolean),
    sa.column("interview", sa.Boolean),
    sa.column("career_paths", postgresql.JSONB),
)
campuses_t = sa.table(
    "campuses", sa.column("id", sa.Integer), sa.column("program_id", sa.Integer), sa.column("name", sa.String)
)
program_requirements_t = sa.table(
    "program_requirements",
    sa.column("id", sa.Integer),
    sa.column("program_id", sa.Integer),
    sa.column("category", sa.String),
    sa.column("rules", postgresql.JSONB),
    sa.column("text_ms", sa.Text),
    sa.column("unparsed", sa.Boolean),
)


def _seed_reference_tables(conn: sa.Connection) -> tuple[dict[str, int], dict[str, int]]:
    """Upsert the hand-written, non-session tables. Returns
    (subject_code -> group id lookup unused, subject_code -> subjects.id,
    university_code -> universities.id)."""
    from app.importer.reference_data import INTEREST_AREAS, UNIVERSITIES
    from app.importer.subjects import SUBJECT_GROUPS, SUBJECTS

    group_ids: dict[str, int] = {
        row.code: row.id for row in conn.execute(sa.select(subject_groups_t.c.code, subject_groups_t.c.id))
    }
    for code, name in SUBJECT_GROUPS.items():
        if code in group_ids:
            continue
        result = conn.execute(sa.insert(subject_groups_t).values(code=code, name=name).returning(subject_groups_t.c.id))
        group_ids[code] = result.scalar_one()

    subject_ids: dict[str, int] = {
        row.code: row.id for row in conn.execute(sa.select(subjects_t.c.code, subjects_t.c.id))
    }
    for subject in SUBJECTS:
        if subject.code in subject_ids:
            continue
        result = conn.execute(
            sa.insert(subjects_t)
            .values(
                code=subject.code,
                name_ms=subject.name_ms,
                name_en=subject.name_en,
                group_id=group_ids[subject.group],
                old_syllabus=subject.old_syllabus,
            )
            .returning(subjects_t.c.id)
        )
        subject_ids[subject.code] = result.scalar_one()

    university_ids: dict[str, int] = {
        row.code: row.id for row in conn.execute(sa.select(universities_t.c.code, universities_t.c.id))
    }
    for code, name in UNIVERSITIES.items():
        if code in university_ids:
            continue
        result = conn.execute(sa.insert(universities_t).values(code=code, name=name).returning(universities_t.c.id))
        university_ids[code] = result.scalar_one()

    existing_areas = {row[0] for row in conn.execute(sa.select(interest_areas_t.c.name))}
    for area in INTEREST_AREAS:
        if area.name in existing_areas:
            continue
        conn.execute(
            sa.insert(interest_areas_t).values(
                name=area.name,
                nec_prefixes=list(area.nec_prefixes),
                exclude_nec_prefixes=list(area.exclude_nec_prefixes),
                subject_groups=list(area.subject_groups),
            )
        )

    return subject_ids, university_ids


def _replace_session_rows(conn: sa.Connection, snapshot: dict) -> int:
    session_name = snapshot["session"]["name"]
    latest_spm_year = snapshot["session"]["latest_spm_year"]

    existing = conn.execute(
        sa.select(sessions_t.c.id).where(sessions_t.c.name == session_name)
    ).scalar_one_or_none()
    if existing is None:
        session_id = conn.execute(
            sa.insert(sessions_t)
            .values(name=session_name, latest_spm_year=latest_spm_year)
            .returning(sessions_t.c.id)
        ).scalar_one()
    else:
        session_id = existing
        conn.execute(
            sa.update(sessions_t).where(sessions_t.c.id == session_id).values(latest_spm_year=latest_spm_year)
        )
        # Replace this session's rows entirely (children first, FKs have no
        # ON DELETE CASCADE): program_requirements -> campuses -> programs ->
        # general_requirements.
        program_ids = [
            row[0] for row in conn.execute(sa.select(programs_t.c.id).where(programs_t.c.session_id == session_id))
        ]
        if program_ids:
            conn.execute(
                sa.delete(program_requirements_t).where(program_requirements_t.c.program_id.in_(program_ids))
            )
            conn.execute(sa.delete(campuses_t).where(campuses_t.c.program_id.in_(program_ids)))
        conn.execute(sa.delete(programs_t).where(programs_t.c.session_id == session_id))
        conn.execute(sa.delete(general_requirements_t).where(general_requirements_t.c.session_id == session_id))

    return session_id


def upgrade() -> None:
    if not SNAPSHOT_PATH.exists():
        raise RuntimeError(
            f"Snapshot not found at {SNAPSHOT_PATH} -- run `uv run python -m "
            "app.importer.epanduan` first (plan Phase 3 task 4)."
        )
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))

    conn = op.get_bind()
    subject_ids, university_ids = _seed_reference_tables(conn)
    session_id = _replace_session_rows(conn, snapshot)

    for category, req in snapshot.get("general_requirements", {}).items():
        conn.execute(
            sa.insert(general_requirements_t).values(
                session_id=session_id,
                category=category,
                rules=req["rules"],
                text_ms=req["text_ms"],
                unparsed=req["unparsed"],
            )
        )

    for program in snapshot["programs"]:
        university_id = university_ids.get(program["university_code"])
        if university_id is None:
            raise RuntimeError(
                f"Program {program['code']!r} has university_code "
                f"{program['university_code']!r}, which is not in "
                "app/importer/reference_data.py UNIVERSITIES."
            )
        program_id = conn.execute(
            sa.insert(programs_t)
            .values(
                session_id=session_id,
                code=program["code"],
                university_id=university_id,
                name=program["name"],
                nec_code=program.get("nec_code"),
                nec_name=program.get("nec_name"),
                level=program.get("level"),
                mode=program.get("mode"),
                duration_value=program.get("duration_value"),
                duration_unit=program.get("duration_unit"),
                avg_merit=program.get("avg_merit"),
                stem=program.get("stem", False),
                tvet=program.get("tvet", False),
                bumiputera_only=program.get("bumiputera_only", False),
                interview=program.get("interview", False),
                career_paths=program.get("career_paths", []),
            )
            .returning(programs_t.c.id)
        ).scalar_one()

        for campus_name in program.get("campuses", []):
            conn.execute(sa.insert(campuses_t).values(program_id=program_id, name=campus_name))

        for category, req in program.get("requirements", {}).items():
            conn.execute(
                sa.insert(program_requirements_t).values(
                    program_id=program_id,
                    category=category,
                    rules=req["rules"],
                    text_ms=req["text_ms"],
                    unparsed=req["unparsed"],
                )
            )


def downgrade() -> None:
    if not SNAPSHOT_PATH.exists():
        return
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    session_name = snapshot["session"]["name"]

    conn = op.get_bind()
    session_id = conn.execute(
        sa.select(sessions_t.c.id).where(sessions_t.c.name == session_name)
    ).scalar_one_or_none()
    if session_id is None:
        return

    program_ids = [
        row[0] for row in conn.execute(sa.select(programs_t.c.id).where(programs_t.c.session_id == session_id))
    ]
    if program_ids:
        conn.execute(sa.delete(program_requirements_t).where(program_requirements_t.c.program_id.in_(program_ids)))
        conn.execute(sa.delete(campuses_t).where(campuses_t.c.program_id.in_(program_ids)))
    conn.execute(sa.delete(programs_t).where(programs_t.c.session_id == session_id))
    conn.execute(sa.delete(general_requirements_t).where(general_requirements_t.c.session_id == session_id))
    conn.execute(sa.delete(sessions_t).where(sessions_t.c.id == session_id))
    # Shared reference tables (universities, subjects, subject_groups,
    # interest_areas) are intentionally left in place -- they are not
    # session-scoped and other sessions may depend on them.
