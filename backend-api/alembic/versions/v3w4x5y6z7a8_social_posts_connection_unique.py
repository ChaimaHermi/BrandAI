"""social_posts: unique per connection, not global post_external_id

Revision ID: v3w4x5y6z7a8
Revises: u2v3w4x5y6z7
Create Date: 2026-06-07
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "v3w4x5y6z7a8"
down_revision: Union[str, Sequence[str], None] = "u2v3w4x5y6z7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_social_posts_post_external_id", table_name="social_posts")
    op.drop_constraint("uq_social_posts_post_external_id", "social_posts", type_="unique")
    op.execute(
        "ALTER TABLE social_posts DROP CONSTRAINT IF EXISTS social_posts_post_external_id_key"
    )
    op.create_unique_constraint(
        "uq_social_posts_connection_post_external_id",
        "social_posts",
        ["connection_id", "post_external_id"],
    )
    op.create_index(
        "ix_social_posts_post_external_id",
        "social_posts",
        ["post_external_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_social_posts_post_external_id", table_name="social_posts")
    op.drop_constraint("uq_social_posts_connection_post_external_id", "social_posts", type_="unique")
    op.create_unique_constraint(
        "uq_social_posts_post_external_id",
        "social_posts",
        ["post_external_id"],
    )
    op.create_index(
        "ix_social_posts_post_external_id",
        "social_posts",
        ["post_external_id"],
        unique=True,
    )
