"""The interest test (PRD T1, T5, T6; plan Phase 4 tasks 1-2):

- `interest_questions` / `interest_options`: the 20 approved questions, each
  with 4 area-tagged options plus one "None of the above" option. Seeded by
  a data migration from `backend/data/upu/../interest_test.json`
  (`backend/data/interest_test.json`) -- never hand-edited, mirroring the
  reference-data replace-by-version pattern (proj-furtherxpert-rules skill
  Section 4). `InterestOption.area_id` is nullable: "None of the above" maps
  to no area (PRD T1: "counts for nothing").
- `interest_answers`: one row per (user, question) -- a student's chosen
  option. `ON DELETE CASCADE` to `users` so `DELETE /me` removes them with no
  extra clean-up code (proj-auth-security skill Section 3). A retake
  replaces all of a user's rows atomically (plan Phase 4 Check;
  `app/services/interest_test.py`).
"""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class InterestQuestion(Base):
    __tablename__ = "interest_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Question number from the approved set (`backend/data/interest_test.json`
    # `questions[].n`), 1-20. Kept only for traceability back to the
    # approved source; the API and `interest_answers` address a question by
    # its `id`.
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


class InterestAnswer(Base):
    __tablename__ = "interest_answers"
    __table_args__ = (UniqueConstraint("user_id", "question_id", name="uq_interest_answers_user_question"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[int] = mapped_column(ForeignKey("interest_questions.id"), nullable=False, index=True)
    chosen_option_id: Mapped[int] = mapped_column(ForeignKey("interest_options.id"), nullable=False, index=True)
