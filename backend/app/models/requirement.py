"""`general_requirements` and `program_requirements` (PRD T2, T5): the UPU
syarat am / syarat khas rule trees, stored per session/program **and per
UPU category** (A/B can differ -- category B may list older-syllabus
subjects, proj-furtherxpert-rules skill §3).

`rules` follows the shape in PRD T2 / the skill's rule-tree table:
`{"all": [...node...], "bumiputera_only": bool, "interview": bool,
"unverifiable": [str, ...]}`. `unparsed` is a structural-failure flag
(plan Phase 3 task 3): true means the importer could not confidently parse
some clause of the original Malay text into the tree, so `text_ms` is kept
for a human to read and the row should be treated conservatively (never
guessed) until reviewed.
"""

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

_CATEGORY_CHECK = "category IN ('A', 'B')"


class GeneralRequirement(Base):
    """Syarat am: the same rule set for every diploma in a session+category
    (verified identical across programs at import time -- plan Phase 3
    task 3).
    """

    __tablename__ = "general_requirements"
    __table_args__ = (
        UniqueConstraint("session_id", "category", name="uq_general_requirements_session_category"),
        CheckConstraint(_CATEGORY_CHECK, name="ck_general_requirements_category"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(1), nullable=False)
    rules: Mapped[dict] = mapped_column(JSONB, nullable=False)
    text_ms: Mapped[str] = mapped_column(Text, nullable=False)
    unparsed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ProgramRequirement(Base):
    """Syarat khas: one rule tree per program per UPU category."""

    __tablename__ = "program_requirements"
    __table_args__ = (
        UniqueConstraint("program_id", "category", name="uq_program_requirements_program_category"),
        CheckConstraint(_CATEGORY_CHECK, name="ck_program_requirements_category"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(1), nullable=False)
    rules: Mapped[dict] = mapped_column(JSONB, nullable=False)
    text_ms: Mapped[str] = mapped_column(Text, nullable=False)
    unparsed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
