"""The `spm_results` table (PRD T5, T6; plan Phase 4 task 2): one row per
subject a student has entered a grade for.

`ON DELETE CASCADE` to `users` (see `app/models/user.py`) means `DELETE /me`
removes these rows with no extra clean-up code. The `grade` CHECK mirrors
`User.race`'s pattern (app/models/user.py): a DB-level defense-in-depth net
behind the API-level validation in `app/schemas/spm_result.py`.
"""

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

# SPM grade set (PRD T1): no B-, C-, or F. Grade points: A+ 9, A 8, A- 7,
# B+ 6, B 5, C+ 4, C 3, D 2, E 1, G 0.
SPM_GRADES = ("A+", "A", "A-", "B+", "B", "C+", "C", "D", "E", "G")


class SPMResult(Base):
    __tablename__ = "spm_results"
    __table_args__ = (
        UniqueConstraint("user_id", "subject_id", name="uq_spm_results_user_subject"),
        CheckConstraint(
            "grade IN ('A+', 'A', 'A-', 'B+', 'B', 'C+', 'C', 'D', 'E', 'G')",
            name="ck_spm_results_grade",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False, index=True)
    grade: Mapped[str] = mapped_column(String(2), nullable=False)
