"""clear analysis cache for why

Revision ID: c9e5a1b63d42
Revises: b8d4f0a52c31
Create Date: 2026-09-14 22:00:00.000000

Phase 10 (result explanations plan Step 10.1 task 5): every Best Fit diploma
in `GET /me/analysis` now carries a `why` explanation. Cached `analysis` rows
were saved without it, so they are deleted once; each student's next visit
recomputes them. No schema change.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c9e5a1b63d42'
down_revision: Union[str, Sequence[str], None] = 'b8d4f0a52c31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('DELETE FROM analysis')


def downgrade() -> None:
    # It's only a cache: nothing to restore.
    pass
