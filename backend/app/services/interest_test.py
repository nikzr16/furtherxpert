"""The interest test: the public question list, and a student's answers
(PRD T1, T6; plan Phase 4 tasks 1, 3, 4).

`list_questions` returns full ORM rows (options included, `id` order =
seeded order) for `app/api/interest_test.py` to serialize through
`InterestQuestionPublic` / `InterestOptionPublic`, which carry no area --
`GET /interest-test` must not leak which option maps to which area (PRD T6).

`save_answers` (PRD T6 `PUT /me/interest-answers`; Phase 6 plan task) is a
**merge/upsert**, not a full replace: each item in the payload updates the
student's existing answer for that question, or inserts a new one -- a
question the payload leaves out keeps whatever the student answered before
(decision `0008`). This is what lets the client save progress as it goes
(plan Phase 6 task 2 "Interest Test... saves progress as-you-go") without
re-sending all 20 answers on every save, and lets a genuine retake of one
question happen without disturbing the rest. A payload does not have to
cover all 20 questions; whether the *stored* answer set (after the merge)
covers all 20 is what `get_progress`'s `complete` flag, and the
`GET /me/analysis` completeness gate (`app/services/analysis.py`), check.

`get_progress` backs the new `GET /me/interest-answers` (Phase 6): it
returns the student's saved answers so far plus whether all 20 questions
are answered yet, so the client can resume a part-finished test and show
progress (e.g. "12 of 20").
"""

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session as DbSession, selectinload

from app.models.analysis import Analysis
from app.models.interest_test import InterestAnswer, InterestOption, InterestQuestion
from app.schemas.interest_test import InterestAnswerIn


class DuplicateQuestionError(Exception):
    def __init__(self, ids: set[int]) -> None:
        self.ids = sorted(ids)
        super().__init__(f"Duplicate question id(s) in payload: {self.ids}")


class UnknownQuestionError(Exception):
    def __init__(self, ids: set[int]) -> None:
        self.ids = sorted(ids)
        super().__init__(f"Unknown question id(s): {self.ids}")


class UnknownOptionError(Exception):
    def __init__(self, ids: set[int]) -> None:
        self.ids = sorted(ids)
        super().__init__(f"Unknown option id(s): {self.ids}")


class OptionQuestionMismatchError(Exception):
    def __init__(self, pairs: list[tuple[int, int]]) -> None:
        self.pairs = pairs
        super().__init__(f"Option(s) do not belong to their question: {pairs}")


def list_questions(db: DbSession) -> list[InterestQuestion]:
    return list(
        db.execute(
            select(InterestQuestion).options(selectinload(InterestQuestion.options)).order_by(InterestQuestion.n)
        ).scalars()
    )


def save_answers(db: DbSession, user_id: uuid.UUID, items: list[InterestAnswerIn]) -> list[dict]:
    question_ids = [item.question_id for item in items]
    seen: set[int] = set()
    duplicate_questions = {q for q in question_ids if q in seen or seen.add(q)}  # type: ignore[func-returns-value]
    if duplicate_questions:
        raise DuplicateQuestionError(duplicate_questions)

    if items:
        question_id_set = set(question_ids)
        known_questions = {
            row.id for row in db.execute(select(InterestQuestion.id).where(InterestQuestion.id.in_(question_id_set)))
        }
        unknown_questions = question_id_set - known_questions
        if unknown_questions:
            raise UnknownQuestionError(unknown_questions)

        option_id_set = {item.option_id for item in items}
        options = {
            row.id: row
            for row in db.execute(select(InterestOption).where(InterestOption.id.in_(option_id_set))).scalars()
        }
        unknown_options = option_id_set - options.keys()
        if unknown_options:
            raise UnknownOptionError(unknown_options)

        mismatched = [
            (item.question_id, item.option_id)
            for item in items
            if options[item.option_id].question_id != item.question_id
        ]
        if mismatched:
            raise OptionQuestionMismatchError(mismatched)

    # Merge/upsert (decision 0008): update the student's existing answer for
    # a payload question, insert a new row otherwise. A question the
    # payload leaves out keeps its previously-saved answer untouched -- this
    # is what makes save-as-you-go / partial saves possible.
    if items:
        existing = {
            row.question_id: row
            for row in db.execute(
                select(InterestAnswer).where(
                    InterestAnswer.user_id == user_id,
                    InterestAnswer.question_id.in_(question_id_set),
                )
            ).scalars()
        }
        for item in items:
            row = existing.get(item.question_id)
            if row is None:
                db.add(InterestAnswer(user_id=user_id, question_id=item.question_id, chosen_option_id=item.option_id))
            else:
                row.chosen_option_id = item.option_id

        # Invalidate the cached analysis (Phase 5): a changed answer set
        # means the cached scores/Best Fit are stale, so the next
        # `GET /me/analysis` must recompute (PRD T5).
        db.execute(delete(Analysis).where(Analysis.user_id == user_id))
    db.commit()

    return [{"question_id": item.question_id, "option_id": item.option_id} for item in items]


def get_progress(db: DbSession, user_id: uuid.UUID) -> dict:
    """The student's saved answers so far, plus whether all 20 questions
    have been answered (Phase 6 `GET /me/interest-answers`)."""
    total_questions = db.execute(select(func.count()).select_from(InterestQuestion)).scalar_one()
    rows = list(db.execute(select(InterestAnswer).where(InterestAnswer.user_id == user_id)).scalars())
    answers = [{"question_id": row.question_id, "option_id": row.chosen_option_id} for row in rows]
    complete = total_questions > 0 and len(rows) >= total_questions
    return {"answers": answers, "complete": complete}
