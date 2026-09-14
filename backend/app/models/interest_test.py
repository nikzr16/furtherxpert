"""The interest test (PRD T1, T5, T6; plan Phase 4 tasks 1-2; Phase 9 rotation
PRD `docs/prd/interest-test-rotation-prd.md`):

- `interest_questions` / `interest_options`: the question bank -- 300
  questions, each with 4 area-tagged options plus one "None of the above"
  option. Loaded by data migrations from `backend/data/interest_test.json`
  -- never hand-edited. `InterestOption.area_id` is nullable: "None of the
  above" maps to no area (PRD T1: "counts for nothing").
- `interest_test_sets` / `interest_test_set_questions` (Phase 9): the 40
  questions one student was given for one attempt, in display order. A set
  is finished once all 40 are answered (`completed_at`), or thrown away by a
  rotate (`discarded_at`). Old sets keep their question list so a new set can
  avoid questions the student has already seen (rotation PRD T3); only their
  answers are deleted. `ON DELETE CASCADE` to `users`.
- `interest_answers`: one row per (set, question) -- a student's chosen
  option. `ON DELETE CASCADE` to both `users` and `interest_test_sets`, so
  `DELETE /me` removes them with no extra clean-up code (proj-auth-security
  skill Section 3).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class InterestQuestion(Base):
    __tablename__ = "interest_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Question number from the bank (`backend/data/interest_test.json`
    # `questions[].n`), 1-300. Kept for traceability back to the source file;
    # the API and `interest_answers` address a question by its `id`.
    n: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    options: Mapped[list["InterestOption"]] = relationship(
        "InterestOption", back_populates="question", cascade="all, delete-orphan", order_by="InterestOption.id"
    )


class InterestOption(Base):
    __tablename__ = "interest_options"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("interest_questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(String, nullable=False)
    # Null for the question's "None of the above" option (PRD T1: "'None of
    # the above' counts for nothing" -- no area to tag).
    area_id: Mapped[int | None] = mapped_column(ForeignKey("interest_areas.id"), nullable=True, index=True)

    question: Mapped["InterestQuestion"] = relationship("InterestQuestion", back_populates="options")


class InterestTestSet(Base):
    __tablename__ = "interest_test_sets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    discarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    questions: Mapped[list["InterestTestSetQuestion"]] = relationship(
        "InterestTestSetQuestion", cascade="all, delete-orphan", order_by="InterestTestSetQuestion.position"
    )


class InterestTestSetQuestion(Base):
    __tablename__ = "interest_test_set_questions"
    __table_args__ = (UniqueConstraint("set_id", "question_id", name="uq_interest_test_set_questions_set_question"),)

    set_id: Mapped[int] = mapped_column(
        ForeignKey("interest_test_sets.id", ondelete="CASCADE"), primary_key=True
    )
    # 1-40: the order the questions are shown in.
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("interest_questions.id"), nullable=False, index=True)


class InterestAnswer(Base):
    __tablename__ = "interest_answers"
    __table_args__ = (UniqueConstraint("set_id", "question_id", name="uq_interest_answers_set_question"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    set_id: Mapped[int] = mapped_column(
        ForeignKey("interest_test_sets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[int] = mapped_column(ForeignKey("interest_questions.id"), nullable=False, index=True)
    chosen_option_id: Mapped[int] = mapped_column(ForeignKey("interest_options.id"), nullable=False, index=True)
