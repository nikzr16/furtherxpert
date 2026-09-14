"""clear analysis cache for dashless text

Revision ID: d1f6b2c74e53
Revises: c9e5a1b63d42
Create Date: 2026-09-14 23:00:00.000000

Decision 0023: "Why this diploma?" explanations and the AI summary no longer
use long dashes. Both are cached on the `analysis` row, so cached rows are
deleted once; each student's next visit rebuilds them. No schema change.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd1f6b2c74e53'
down_revision: Union[str, Sequence[str], None] = 'c9e5a1b63d42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('DELETE FROM analysis')


def downgrade() -> None:
    # It's only a cache: nothing to restore.
    pass
