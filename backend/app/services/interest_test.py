"""The interest test: the public question list, and a student's answers
(PRD T1, T6; plan Phase 4 tasks 1, 3, 4).

`list_questions` returns full ORM rows (options included, `id` order =
seeded order) for `app/api/interest_test.py` to serialize through
`InterestQuestionPublic` / `InterestOptionPublic`, which carry no area --
`GET /interest-test` must not leak which option maps to which area (PRD T6).

`replace_answers` is the "retake" (PRD T6 `PUT /me/interest-answers`, plan
Phase 4 Check): it deletes every existing answer for the user and inserts
the payload's rows in the same transaction, so a retake never leaves a mix
of old and new answers. The payload does not have to cover all 20 questions
(plan Phase 4 task 4 says "one answer per **answered** question", not "every
question") -- whatever subset is sent becomes the user's full new answer
set.
"""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DbSession, selectinload

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


def replace_answers(db: DbSession, user_id: uuid.UUID, items: list[InterestAnswerIn]) -> list[dict]:
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

    # Atomic retake: clear every previous answer for this user, then insert
    # the new set, in one transaction (plan Phase 4 Check).
    db.execute(delete(InterestAnswer).where(InterestAnswer.user_id == user_id))
    for item in items:
        db.add(InterestAnswer(user_id=user_id, question_id=item.question_id, chosen_option_id=item.option_id))
    db.commit()

    return [{"question_id": item.question_id, "option_id": item.option_id} for item in items]
