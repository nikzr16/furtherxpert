"""`subject_groups` and `subjects` (PRD T1, T5).

Both are seeded from `app/importer/subjects.py`'s hand-written list, not
scraped. `Subject.old_syllabus` flags a name category B candidates may still
hold but that no longer appears for this year's leavers (proj-furtherxpert-rules
skill §4).
"""

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class SubjectGroup(Base):
    __tablename__ = "subject_groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Stable short code, e.g. "SCIENCES" (app/importer/subjects.py).
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name_ms: Mapped[str] = mapped_column(String, nullable=False)
    name_en: Mapped[str] = mapped_column(String, nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("subject_groups.id"), nullable=False)
    old_syllabus: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
