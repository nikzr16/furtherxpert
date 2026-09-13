"""add ai summary columns to analysis

Revision ID: 96f63a9f3e5c
Revises: 3916bef04fb3
Create Date: 2026-09-14 01:35:25.076548

Phase 7 (PRD T4, T7; plan Phase 7 task 2): two nullable columns on the
existing `analysis` cache row so the AI summary is invalidated for free by
the same unconditional delete `app/services/results.py` / `interest_test.py`
already perform on results/answer changes (see `app/models/analysis.py`).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96f63a9f3e5c'
down_revision: Union[str, Sequence[str], None] = '3916bef04fb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('analysis', sa.Column('summary', sa.Text(), nullable=True))
    op.add_column('analysis', sa.Column('summary_computed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('analysis', 'summary_computed_at')
    op.drop_column('analysis', 'summary')
