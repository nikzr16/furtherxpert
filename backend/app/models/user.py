"""The `users` table (PRD T3 login, T4 privacy, T5 data).

`users.id` is a UUID primary key with no other meaning, so the Phase 4
student tables (`spm_results`, `interest_answers`, `analysis`) can each add
`user_id UUID REFERENCES users(id) ON DELETE CASCADE`: deleting a user (the
PDPA "delete my account" request, `DELETE /me`) then removes every row that
depends on it in one cascade, with no per-table clean-up code needed.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.db import Base

# UPU's race categories (PRD T4): used only to check Bumiputera-only
# programs. Bumiputera = Melayu, Anak Negeri Sabah, Anak Negeri Sarawak,
# Orang Asli (Domain Rule 8).
RACES = (
    "Melayu",
    "Cina",
    "India",
    "Anak Negeri Sabah",
    "Anak Negeri Sarawak",
    "Orang Asli",
    "Lain-lain",
)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "race IN ('Melayu', 'Cina', 'India', 'Anak Negeri Sabah', "
            "'Anak Negeri Sarawak', 'Orang Asli', 'Lain-lain')",
            name="ck_users_race",
        ),
        # Wide sanity net only; the tight "current-ish year" rule is
        # enforced at the Pydantic schema level (app/schemas/user.py), since
        # "current" moves every year and a CHECK constraint should not.
        CheckConstraint("spm_year >= 1970 AND spm_year <= 2100", name="ck_users_spm_year_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_citizen: Mapped[bool] = mapped_column(Boolean, nullable=False)
    race: Mapped[str] = mapped_column(String, nullable=False)
    spm_year: Mapped[int] = mapped_column(Integer, nullable=False)
    # Registration requires consent (app/schemas/user.py); this records when.
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
