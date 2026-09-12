"""The `interest_areas` table (PRD T1): NEC-code-prefix -> area, and the
subject groups used for that area's "excel" score. Seeded from
`app/importer/reference_data.py`'s hand-written table (PRD T1), not scraped.

Phase 4's `interest_questions` / `interest_options` (out of scope here) will
each tag an answer to exactly one of these areas.
"""

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class InterestArea(Base):
    __tablename__ = "interest_areas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    # List[str] of NEC prefixes this area matches, e.g. ["05", "06", "07"].
    nec_prefixes: Mapped[list] = mapped_column(JSONB, nullable=False)
    # List[str] of NEC prefixes excluded even though a broader prefix above
    # matches (PRD T1: "05 (except 052)").
    exclude_nec_prefixes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # List[str] of subject_groups.code used for this area's "excel" score.
    subject_groups: Mapped[list] = mapped_column(JSONB, nullable=False)
