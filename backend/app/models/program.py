"""`programs` and `campuses` (PRD T5): UA diploma programs for a session,
loaded from an e-Panduan snapshot (`backend/data/upu/<session>.json`) by a
data migration -- never hand-edited (plan Phase 3 task 5).

`bumiputera_only` / `interview` here are program-level flags for filtering
and badges; the grade-checkable rule tree (with the same two flags, per
category) lives in `ProgramRequirement.rules` (app/models/requirement.py).
"""

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Program(Base):
    __tablename__ = "programs"
    __table_args__ = (UniqueConstraint("session_id", "code", name="uq_programs_session_code"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False, index=True)
    # e.g. "UE4481001". Matches ^U[A-Z]4 -- UA diploma codes only (plan
    # Phase 3 task 3).
    code: Mapped[str] = mapped_column(String, nullable=False, index=True)
    university_id: Mapped[int] = mapped_column(ForeignKey("universities.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    nec_code: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    nec_name: Mapped[str | None] = mapped_column(String, nullable=True)

    level: Mapped[str | None] = mapped_column(String, nullable=True)  # "Peringkat Pengajian"
    mode: Mapped[str | None] = mapped_column(String, nullable=True)  # "Mod Pengajian"
    duration_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_unit: Mapped[str | None] = mapped_column(String, nullable=True)  # "Semester" | "Tahun"

    avg_merit: Mapped[float | None] = mapped_column(Float, nullable=True)  # percent, e.g. 68.38

    stem: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tvet: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    bumiputera_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    interview: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # List[str] career paths ("laluan kerjaya"); [] if e-Panduan listed none.
    career_paths: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    campuses: Mapped[list["Campus"]] = relationship(
        "Campus", back_populates="program", cascade="all, delete-orphan"
    )


class Campus(Base):
    __tablename__ = "campuses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    program: Mapped["Program"] = relationship("Program", back_populates="campuses")
