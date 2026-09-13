"""The `analysis` table (PRD T5): a per-user cache of the computed charts,
Best Fit, category, and (Phase 7) the AI summary. One row per user
(`user_id` is the primary key, not a surrogate `id`) -- a fresh computation
replaces the row rather than accumulating history.

`ON DELETE CASCADE` to `users` (mirrors `spm_result.py` / `interest_test.py`'s
FK style) so `DELETE /me` removes it with no extra clean-up code
(proj-auth-security skill Section 3). `result` is the full response payload
`GET /me/analysis` returns (see `app/services/analysis.py` for the exact
shape); `computed_at` is kept as its own real `DateTime` column (redundant
with `result["computed_at"]`) so a caller can order/filter by it without
parsing JSONB.

`summary` / `summary_computed_at` (Phase 7, PRD T4/T7) cache the AI summary
text for `GET /me/analysis/summary` (`app/services/analysis.py`,
`get_analysis_summary`). They're nullable columns on this same row rather
than a separate table: the whole row -- charts and summary together -- is
already deleted and recomputed together whenever the student's data
changes (see below), so nesting the summary here gets that invalidation for
free instead of needing a second cache-invalidation path.

Cache invalidation is not this module's job: `app/services/results.py`
(`upsert_results`) and `app/services/interest_test.py` (`save_answers`)
delete a user's row here whenever their SPM results or interest answers
change, so the next `GET /me/analysis` (and therefore the next
`GET /me/analysis/summary`) recomputes both the charts and the summary.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Analysis(Base):
    __tablename__ = "analysis"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Phase 7: the cached AI summary text for this same (unchanged)
    # analysis, and when it was generated. NULL until the first
    # `GET /me/analysis/summary` call for this row generates one.
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_computed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
