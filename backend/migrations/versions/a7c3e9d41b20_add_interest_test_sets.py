"""add interest test sets

Revision ID: a7c3e9d41b20
Revises: 96f63a9f3e5c
Create Date: 2026-09-14 20:00:00.000000

Phase 9 (rotation PRD T2-T3; plan Step 9.2 task 1): each student gets their
own 40-question set. Adds `interest_test_sets` and
`interest_test_set_questions`, and ties every `interest_answers` row to a set
(`set_id`), so the unique rule moves from (user, question) to (set, question).

Existing answers belong to no set, so they are deleted first, and every cached
`analysis` row is cleared so scores are recomputed. There are no real users
yet, so no real results are lost (rotation PRD section 7).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7c3e9d41b20'
down_revision: Union[str, Sequence[str], None] = '96f63a9f3e5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('interest_test_sets',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('discarded_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interest_test_sets_user_id'), 'interest_test_sets', ['user_id'], unique=False)
    op.create_table('interest_test_set_questions',
    sa.Column('set_id', sa.Integer(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['question_id'], ['interest_questions.id'], ),
    sa.ForeignKeyConstraint(['set_id'], ['interest_test_sets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('set_id', 'position'),
    sa.UniqueConstraint('set_id', 'question_id', name='uq_interest_test_set_questions_set_question')
    )
    op.create_index(
        op.f('ix_interest_test_set_questions_question_id'), 'interest_test_set_questions', ['question_id'], unique=False
    )

    op.execute('DELETE FROM interest_answers')
    op.execute('DELETE FROM analysis')

    op.add_column('interest_answers', sa.Column('set_id', sa.Integer(), nullable=False))
    op.create_index(op.f('ix_interest_answers_set_id'), 'interest_answers', ['set_id'], unique=False)
    op.create_foreign_key(
        'fk_interest_answers_set_id', 'interest_answers', 'interest_test_sets', ['set_id'], ['id'], ondelete='CASCADE'
    )
    op.drop_constraint('uq_interest_answers_user_question', 'interest_answers', type_='unique')
    op.create_unique_constraint('uq_interest_answers_set_question', 'interest_answers', ['set_id', 'question_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Set-based answers can't be mapped back to the old one-list-per-user
    # shape, so they are dropped, like the upgrade drops the old ones.
    op.execute('DELETE FROM interest_answers')
    op.execute('DELETE FROM analysis')
    op.drop_constraint('uq_interest_answers_set_question', 'interest_answers', type_='unique')
    op.create_unique_constraint('uq_interest_answers_user_question', 'interest_answers', ['user_id', 'question_id'])
    op.drop_constraint('fk_interest_answers_set_id', 'interest_answers', type_='foreignkey')
    op.drop_index(op.f('ix_interest_answers_set_id'), table_name='interest_answers')
    op.drop_column('interest_answers', 'set_id')
    op.drop_index(op.f('ix_interest_test_set_questions_question_id'), table_name='interest_test_set_questions')
    op.drop_table('interest_test_set_questions')
    op.drop_index(op.f('ix_interest_test_sets_user_id'), table_name='interest_test_sets')
    op.drop_table('interest_test_sets')
