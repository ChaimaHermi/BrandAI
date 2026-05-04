"""linkedin_url column; drop account_url on user_social_connections

Revision ID: r0s1t2u3v4w5
Revises: q9r0s1t2u3v4
Create Date: 2026-05-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision: str = "r0s1t2u3v4w5"
down_revision: Union[str, Sequence[str], None] = "q9r0s1t2u3v4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = {c["name"] for c in insp.get_columns("user_social_connections")}

    if "linkedin_url" not in existing:
        op.add_column(
            "user_social_connections",
            sa.Column("linkedin_url", sa.String(length=1024), nullable=True),
        )
        existing.add("linkedin_url")

    if "account_url" in existing:
        op.execute(
            text(
                """
                UPDATE user_social_connections
                SET linkedin_url = account_url
                WHERE provider = 'linkedin'
                  AND (linkedin_url IS NULL OR linkedin_url = '')
                  AND account_url IS NOT NULL
                  AND account_url != ''
                """
            )
        )
        op.drop_column("user_social_connections", "account_url")


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = {c["name"] for c in insp.get_columns("user_social_connections")}

    if "account_url" not in existing:
        op.add_column(
            "user_social_connections",
            sa.Column("account_url", sa.String(length=1024), nullable=True),
        )
        existing.add("account_url")

    if "linkedin_url" in existing:
        op.execute(
            text(
                """
                UPDATE user_social_connections
                SET account_url = linkedin_url
                WHERE provider = 'linkedin'
                  AND (account_url IS NULL OR account_url = '')
                  AND linkedin_url IS NOT NULL
                  AND linkedin_url != ''
                """
            )
        )
        op.drop_column("user_social_connections", "linkedin_url")
