"""add result_names, result_slogans, result_logo to brand_identity

Revision ID: i0j1k2l3m4n5
Revises: g8h9i0j1k2l3
Create Date: 2026-04-04

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "i0j1k2l3m4n5"
down_revision: Union[str, Sequence[str], None] = "g8h9i0j1k2l3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "brand_identity",
        sa.Column("result_names", sa.JSON(), nullable=True),
    )
    op.add_column(
        "brand_identity",
        sa.Column("result_slogans", sa.JSON(), nullable=True),
    )
    op.add_column(
        "brand_identity",
        sa.Column("result_logo", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("brand_identity", "result_logo")
    op.drop_column("brand_identity", "result_slogans")
    op.drop_column("brand_identity", "result_names")
