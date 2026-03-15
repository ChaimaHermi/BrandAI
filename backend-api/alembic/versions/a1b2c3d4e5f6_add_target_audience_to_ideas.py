"""add target_audience to ideas

Revision ID: a1b2c3d4e5f6
Revises: 7903dd36eaf8
Create Date: 2026-03-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "7903dd36eaf8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ideas", sa.Column("target_audience", sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column("ideas", "target_audience")
