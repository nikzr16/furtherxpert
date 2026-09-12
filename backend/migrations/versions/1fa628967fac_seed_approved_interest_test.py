"""seed approved interest test

Revision ID: 1fa628967fac
Revises: 23947a34f766
Create Date: 2026-09-12 12:54:32.069352

Phase 4 (PRD T1, T5, T6; plan Phase 4 tasks 1 and 3): loads the product
owner-approved 20 questions from `backend/data/interest_test.json` into
`interest_questions` / `interest_options`, tagging each option to its area
via the already-seeded `interest_areas` table (Phase 3). Each question also
gets one untagged "None of the above" option (`area_id` NULL -- PRD T1:
"'None of the above' counts for nothing").

Same replace pattern as the UPU snapshot data migration
(`6676e66b52e5_load_2026_2027_upu_snapshot.py`): re-running this migration
(for example after the approved question set changes) deletes every
existing `interest_options` / `interest_questions` row first, then reloads
the file fresh, so the two tables always mirror the committed JSON exactly.
There is only ever one active interest test -- unlike UPU sessions, which
can coexist by name, this migration does not key its replace on the file's
`version` field; it always fully replaces the whole set (see the build
report for this trade-off).
"""
import json
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '1fa628967fac'
down_revision: Union[str, Sequence[str], None] = '23947a34f766'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "interest_test.json"

# --- Lightweight table mirrors (data migrations should not import the ORM
# models, which can change shape after this revision is written) ---

interest_areas_t = sa.table("interest_areas", sa.column("id", sa.Integer), sa.column("name", sa.String))
interest_questions_t = sa.table(
    "interest_questions", sa.column("id", sa.Integer), sa.column("n", sa.Integer), sa.column("text", sa.Text)
)
interest_options_t = sa.table(
    "interest_options",
    sa.column("id", sa.Integer),
    sa.column("question_id", sa.Integer),
    sa.column("text", sa.String),
    sa.column("area_id", sa.Integer),
)


def _clear_existing(conn: sa.Connection) -> None:
    # Children first: interest_options has no ON DELETE CASCADE from
    # interest_questions in the other direction needed here (this migration
    # deletes both explicitly, matching the UPU loader's own delete order).
    conn.execute(sa.delete(interest_options_t))
    conn.execute(sa.delete(interest_questions_t))


def upgrade() -> None:
    if not DATA_PATH.exists():
        raise RuntimeError(
            f"Approved interest test not found at {DATA_PATH} -- it must be drafted in "
            "chat and approved by the product owner before seeding (plan Phase 4 task 1)."
        )
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    conn = op.get_bind()

    area_ids: dict[str, int] = {
        row.name: row.id for row in conn.execute(sa.select(interest_areas_t.c.name, interest_areas_t.c.id))
    }
    area_codes_to_names: dict[str, str] = data["areas"]
    unknown_area_names = {name for name in area_codes_to_names.values() if name not in area_ids}
    if unknown_area_names:
        raise RuntimeError(
            f"interest_test.json references area name(s) not found in interest_areas: "
            f"{sorted(unknown_area_names)} -- run the Phase 3 reference-data migration first."
        )

    _clear_existing(conn)

    none_option_text = data["none_option"]
    for question in data["questions"]:
        question_id = conn.execute(
            sa.insert(interest_questions_t)
            .values(n=question["n"], text=question["text"])
            .returning(interest_questions_t.c.id)
        ).scalar_one()

        for option_text, area_code in question["options"]:
            area_id = area_ids[area_codes_to_names[area_code]]
            conn.execute(
                sa.insert(interest_options_t).values(question_id=question_id, text=option_text, area_id=area_id)
            )

        # PRD T1: every question also offers "None of the above", which
        # counts toward no area.
        conn.execute(
            sa.insert(interest_options_t).values(question_id=question_id, text=none_option_text, area_id=None)
        )


def downgrade() -> None:
    conn = op.get_bind()
    _clear_existing(conn)
