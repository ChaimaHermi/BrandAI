"""add clarity fields to ideas

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6g7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ideas", sa.Column("clarity_status", sa.String(50), nullable=True))
    op.add_column("ideas", sa.Column("clarity_score", sa.Integer(), nullable=True))
    op.add_column("ideas", sa.Column("clarity_sector", sa.String(200), nullable=True))
    op.add_column("ideas", sa.Column("clarity_target_users", sa.String(500), nullable=True))
    op.add_column("ideas", sa.Column("clarity_problem", sa.Text(), nullable=True))
    op.add_column("ideas", sa.Column("clarity_solution", sa.Text(), nullable=True))
    op.add_column("ideas", sa.Column("clarity_short_pitch", sa.String(500), nullable=True))
    op.add_column("ideas", sa.Column("clarity_agent_message", sa.Text(), nullable=True))
    op.add_column("ideas", sa.Column("clarity_questions", sa.JSON(), nullable=True))
    op.add_column("ideas", sa.Column("clarity_answers", sa.JSON(), nullable=True))
    op.add_column("ideas", sa.Column("clarity_refused_reason", sa.String(200), nullable=True))
    op.add_column("ideas", sa.Column("clarity_refused_message", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("ideas", "clarity_refused_message")
    op.drop_column("ideas", "clarity_refused_reason")
    op.drop_column("ideas", "clarity_answers")
    op.drop_column("ideas", "clarity_questions")
    op.drop_column("ideas", "clarity_agent_message")
    op.drop_column("ideas", "clarity_short_pitch")
    op.drop_column("ideas", "clarity_solution")
    op.drop_column("ideas", "clarity_problem")
    op.drop_column("ideas", "clarity_target_users")
    op.drop_column("ideas", "clarity_sector")
    op.drop_column("ideas", "clarity_score")
    op.drop_column("ideas", "clarity_status")
