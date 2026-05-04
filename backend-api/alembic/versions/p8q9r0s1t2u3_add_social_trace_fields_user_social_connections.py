"""add account_name page_name account_url to user_social_connections

Revision ID: p8q9r0s1t2u3
Revises: o7p8q9r0s1t2
Create Date: 2026-05-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "p8q9r0s1t2u3"
down_revision: Union[str, Sequence[str], None] = "o7p8q9r0s1t2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = {c["name"] for c in insp.get_columns("user_social_connections")}
    if "account_name" not in existing:
        op.add_column(
            "user_social_connections",
            sa.Column("account_name", sa.String(length=255), nullable=True),
        )
    if "page_name" not in existing:
        op.add_column(
            "user_social_connections",
            sa.Column("page_name", sa.String(length=512), nullable=True),
        )
    if "account_url" not in existing:
        op.add_column(
            "user_social_connections",
            sa.Column("account_url", sa.String(length=1024), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = {c["name"] for c in insp.get_columns("user_social_connections")}
    if "account_url" in existing:
        op.drop_column("user_social_connections", "account_url")
    if "page_name" in existing:
        op.drop_column("user_social_connections", "page_name")
    if "account_name" in existing:
        op.drop_column("user_social_connections", "account_name")
