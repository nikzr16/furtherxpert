"""The `universities` table: UPU's public-university (UA) codes and names."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class University(Base):
    __tablename__ = "universities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # e.g. "UE" -> "Universiti Teknologi Mara". Codes are stable across
    # sessions (app/importer/reference_data.py), so universities are not
    # session-scoped like programs.
    code: Mapped[str] = mapped_column(String(4), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
