"""add facebook_url and instagram_url to user_social_connections

Revision ID: q9r0s1t2u3v4
Revises: p8q9r0s1t2u3
Create Date: 2026-05-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "q9r0s1t2u3v4"
down_revision: Union[str, Sequence[str], None] = "p8q9r0s1t2u3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = {c["name"] for c in insp.get_columns("user_social_connections")}
    if "facebook_url" not in existing:
        op.add_column(
            "user_social_connections",
            sa.Column("facebook_url", sa.String(length=1024), nullable=True),
        )
    if "instagram_url" not in existing:
        op.add_column(
            "user_social_connections",
            sa.Column("instagram_url", sa.String(length=1024), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = {c["name"] for c in insp.get_columns("user_social_connections")}
    if "instagram_url" in existing:
        op.drop_column("user_social_connections", "instagram_url")
    if "facebook_url" in existing:
        op.drop_column("user_social_connections", "facebook_url")
