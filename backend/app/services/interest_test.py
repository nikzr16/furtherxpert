"""The interest test: a student's question set, rotation, and answers
(PRD T1, T6; rotation PRD `docs/prd/interest-test-rotation-prd.md` T2-T3;
rotation plan Processing Flows A, B, D).

- `get_or_create_current_set` backs `GET /me/interest-test`. It returns the
  student's latest set, or draws a new one when there is none or the latest
  one is finished. A part-finished set is always resumed.
- `rotate_set` backs `POST /me/interest-test/rotate`. It throws away an
  unfinished set (its answers are deleted, its question list is kept as
  "seen" history) and draws a new one.
- `save_answers` backs `PUT /me/interest-answers`. It is a **merge/upsert**
  (decision `0008`): a question the payload leaves out keeps its saved
  answer. Only questions in the current set are accepted. When the 40th
  answer lands, the set is marked finished and the answers of any older set
  are deleted (rotation PRD section 6: keep only the answers still needed).
- `get_progress` backs `GET /me/interest-answers`. It never creates a set.

The public responses never carry an option's area (PRD T6).
"""

import logging
import random
import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session as DbSession, selectinload

from app.models.analysis import Analysis
from app.models.interest_test import (
    InterestAnswer,
    InterestOption,
    InterestQuestion,
    InterestTestSet,
    InterestTestSetQuestion,
)
from app.models.user import User
from app.schemas.interest_test import InterestAnswerIn
from app.services.question_sets import draw_set, is_balanced

logger = logging.getLogger(__name__)


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


class QuestionNotInSetError(Exception):
    def __init__(self, ids: set[int]) -> None:
        self.ids = sorted(ids)
        super().__init__(f"Question(s) not in your current interest test set: {self.ids}")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _lock_user(db: DbSession, user_id: uuid.UUID) -> None:
    """Row-lock the student so two tabs can't create two sets at once."""
    db.execute(select(User.id).where(User.id == user_id).with_for_update())


def _latest_set(db: DbSession, user_id: uuid.UUID) -> InterestTestSet | None:
    return db.execute(
        select(InterestTestSet)
        .where(InterestTestSet.user_id == user_id)
        .order_by(InterestTestSet.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def _create_set(db: DbSession, user_id: uuid.UUID) -> InterestTestSet:
    question_areas: dict[int, set[int]] = {}
    for question_id, area_id in db.execute(
        select(InterestOption.question_id, InterestOption.area_id).where(InterestOption.area_id.isnot(None))
    ):
        question_areas.setdefault(question_id, set()).add(area_id)

    past_sets = [
        [row.question_id for row in past.questions]
        for past in db.execute(
            select(InterestTestSet)
            .where(InterestTestSet.user_id == user_id)
            .options(selectinload(InterestTestSet.questions))
            .order_by(InterestTestSet.id)
        ).scalars()
    ]

    question_ids = draw_set(question_areas, past_sets, random.Random())
    if not is_balanced(question_ids, question_areas):
        # No student data in the log: only that the balance range was missed.
        logger.warning("Drew an interest test set outside the per-area balance range")

    new_set = InterestTestSet(user_id=user_id)
    db.add(new_set)
    db.flush()
    for position, question_id in enumerate(question_ids, start=1):
        db.add(InterestTestSetQuestion(set_id=new_set.id, position=position, question_id=question_id))
    db.flush()
    return new_set


def _set_payload(db: DbSession, test_set: InterestTestSet) -> dict:
    questions = list(
        db.execute(
            select(InterestQuestion)
            .join(InterestTestSetQuestion, InterestTestSetQuestion.question_id == InterestQuestion.id)
            .where(InterestTestSetQuestion.set_id == test_set.id)
            .options(selectinload(InterestQuestion.options))
            .order_by(InterestTestSetQuestion.position)
        ).scalars()
    )
    answers = [
        {"question_id": row.question_id, "option_id": row.chosen_option_id}
        for row in db.execute(select(InterestAnswer).where(InterestAnswer.set_id == test_set.id)).scalars()
    ]
    has_finished_set = (
        db.execute(
            select(func.count())
            .select_from(InterestTestSet)
            .where(
                InterestTestSet.user_id == test_set.user_id,
                InterestTestSet.completed_at.isnot(None),
                InterestTestSet.id != test_set.id,
            )
        ).scalar_one()
        > 0
    )
    return {
        "set_id": test_set.id,
        "questions": questions,
        "answers": answers,
        "answered": len(answers),
        "total": len(questions),
        "complete": test_set.completed_at is not None,
        "has_finished_set": has_finished_set,
    }


def get_or_create_current_set(db: DbSession, user_id: uuid.UUID) -> dict:
    _lock_user(db, user_id)
    current = _latest_set(db, user_id)
    if current is None or current.completed_at is not None:
        current = _create_set(db, user_id)
    payload = _set_payload(db, current)
    db.commit()
    return payload


def rotate_set(db: DbSession, user_id: uuid.UUID) -> dict:
    _lock_user(db, user_id)
    current = _latest_set(db, user_id)
    if current is not None and current.completed_at is None:
        current.discarded_at = _now()
        db.execute(delete(InterestAnswer).where(InterestAnswer.set_id == current.id))
    new_set = _create_set(db, user_id)
    db.execute(delete(Analysis).where(Analysis.user_id == user_id))
    payload = _set_payload(db, new_set)
    db.commit()
    return payload


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

        current = _latest_set(db, user_id)
        set_question_ids = (
            set(
                db.execute(
                    select(InterestTestSetQuestion.question_id).where(InterestTestSetQuestion.set_id == current.id)
                ).scalars()
            )
            if current is not None
            else set()
        )
        outside_set = question_id_set - set_question_ids
        if outside_set:
            raise QuestionNotInSetError(outside_set)

        # Merge/upsert (decision 0008): update the saved answer for a payload
        # question, insert a new row otherwise. A question the payload leaves
        # out keeps its previously saved answer.
        existing = {
            row.question_id: row
            for row in db.execute(
                select(InterestAnswer).where(
                    InterestAnswer.set_id == current.id,
                    InterestAnswer.question_id.in_(question_id_set),
                )
            ).scalars()
        }
        for item in items:
            row = existing.get(item.question_id)
            if row is None:
                db.add(
                    InterestAnswer(
                        user_id=user_id,
                        set_id=current.id,
                        question_id=item.question_id,
                        chosen_option_id=item.option_id,
                    )
                )
            else:
                row.chosen_option_id = item.option_id
        db.flush()

        answered = db.execute(
            select(func.count()).select_from(InterestAnswer).where(InterestAnswer.set_id == current.id)
        ).scalar_one()
        if current.completed_at is None and answered >= len(set_question_ids):
            current.completed_at = _now()
            # Only the newest finished set's answers are still needed
            # (rotation PRD section 6). Discarded sets' answers are already gone.
            db.execute(
                delete(InterestAnswer).where(InterestAnswer.user_id == user_id, InterestAnswer.set_id != current.id)
            )

        # Invalidate the cached analysis (Phase 5): the next
        # `GET /me/analysis` recomputes (PRD T5).
        db.execute(delete(Analysis).where(Analysis.user_id == user_id))
    db.commit()

    return [{"question_id": item.question_id, "option_id": item.option_id} for item in items]


def get_progress(db: DbSession, user_id: uuid.UUID) -> dict:
    """Saved answers for the current set, and whether it's finished. Never
    creates a set (`GET /me/interest-answers`)."""
    current = _latest_set(db, user_id)
    if current is None:
        return {"answers": [], "complete": False}
    rows = db.execute(select(InterestAnswer).where(InterestAnswer.set_id == current.id)).scalars()
    answers = [{"question_id": row.question_id, "option_id": row.chosen_option_id} for row in rows]
    return {"answers": answers, "complete": current.completed_at is not None}
