"""The `sessions` table: one row per UPU intake session (PRD T5).

`latest_spm_year` is the SPM year that counts as category A for this session
(PRD T2: "The latest SPM for the loaded session is A ... Any earlier year is
B"). A new yearly import adds a new session and its own reference rows; the
data migration that loads a session's snapshot replaces that session's rows
only (plan Phase 3 task 5).
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.db import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # e.g. "2026/2027".
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    latest_spm_year: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
