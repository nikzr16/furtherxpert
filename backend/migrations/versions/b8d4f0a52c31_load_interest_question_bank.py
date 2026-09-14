"""load interest question bank

Revision ID: b8d4f0a52c31
Revises: a7c3e9d41b20
Create Date: 2026-09-14 20:05:00.000000

Phase 9 (rotation PRD section 3; plan Step 9.2 task 2): grows the interest
test from 20 questions to the 300-question bank in
`backend/data/interest_test.json`.

Unlike the Phase 4 seed (`1fa628967fac`), this migration **appends**: it
inserts only questions whose number (`n`) is not in the database yet, and
leaves existing questions alone. Questions 1-20 keep their ids, so nothing
that points at them breaks (the risk decision `0004` warns about). Safe to
re-run.

On a brand-new database, `1fa628967fac` already reads the same (now
300-question) file, so this migration finds nothing left to insert. Either
way the database ends up with the same 300 questions.
"""
import json
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b8d4f0a52c31'
down_revision: Union[str, Sequence[str], None] = 'a7c3e9d41b20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "interest_test.json"

# The first 20 questions came from the Phase 4 seed; downgrade removes the rest.
ORIGINAL_QUESTION_COUNT = 20

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


def upgrade() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    conn = op.get_bind()

    area_ids: dict[str, int] = {
        row.name: row.id for row in conn.execute(sa.select(interest_areas_t.c.name, interest_areas_t.c.id))
    }
    area_codes_to_names: dict[str, str] = data["areas"]
    unknown_area_names = {name for name in area_codes_to_names.values() if name not in area_ids}
    if unknown_area_names:
        raise RuntimeError(f"interest_test.json references unknown area name(s): {sorted(unknown_area_names)}")

    existing_ns = {row.n for row in conn.execute(sa.select(interest_questions_t.c.n))}
    none_option_text = data["none_option"]

    for question in data["questions"]:
        if question["n"] in existing_ns:
            continue
        question_id = conn.execute(
            sa.insert(interest_questions_t)
            .values(n=question["n"], text=question["text"])
            .returning(interest_questions_t.c.id)
        ).scalar_one()
        for option_text, area_code in question["options"]:
            conn.execute(
                sa.insert(interest_options_t).values(
                    question_id=question_id, text=option_text, area_id=area_ids[area_codes_to_names[area_code]]
                )
            )
        # PRD T1: every question also offers "None of the above", which
        # counts toward no area.
        conn.execute(
            sa.insert(interest_options_t).values(question_id=question_id, text=none_option_text, area_id=None)
        )


def downgrade() -> None:
    conn = op.get_bind()
    # Sets and answers may point at the questions being removed.
    conn.execute(sa.text("DELETE FROM interest_answers"))
    conn.execute(sa.text("DELETE FROM interest_test_sets"))
    conn.execute(sa.text("DELETE FROM analysis"))
    extra_ids = sa.select(interest_questions_t.c.id).where(interest_questions_t.c.n > ORIGINAL_QUESTION_COUNT)
    conn.execute(sa.delete(interest_options_t).where(interest_options_t.c.question_id.in_(extra_ids)))
    conn.execute(sa.delete(interest_questions_t).where(interest_questions_t.c.n > ORIGINAL_QUESTION_COUNT))
