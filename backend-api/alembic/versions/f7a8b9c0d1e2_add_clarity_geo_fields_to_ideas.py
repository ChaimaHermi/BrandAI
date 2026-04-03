"""add clarity geo fields to ideas

Revision ID: f7a8b9c0d1e2
Revises: e6f7g8h9i0j1
Create Date: 2026-04-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, Sequence[str], None] = "e6f7g8h9i0j1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ideas", sa.Column("clarity_country", sa.String(length=120), nullable=True))
    op.add_column("ideas", sa.Column("clarity_country_code", sa.String(length=8), nullable=True))
    op.add_column("ideas", sa.Column("clarity_language", sa.String(length=8), nullable=True))


def downgrade() -> None:
    op.drop_column("ideas", "clarity_language")
    op.drop_column("ideas", "clarity_country_code")
    op.drop_column("ideas", "clarity_country")
