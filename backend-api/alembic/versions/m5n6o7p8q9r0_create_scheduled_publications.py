"""create scheduled_publications for content calendar / future auto-publish

Revision ID: m5n6o7p8q9r0
Revises: l4m5n6o7p8q9
Create Date: 2026-04-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "m5n6o7p8q9r0"
down_revision: Union[str, Sequence[str], None] = "l4m5n6o7p8q9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scheduled_publications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("idea_id", sa.Integer(), nullable=False),
        sa.Column("generated_content_id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("caption_snapshot", sa.Text(), nullable=False),
        sa.Column("image_url_snapshot", sa.Text(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=True, server_default="UTC"),
        sa.Column(
            "status",
            sa.String(length=24),
            nullable=False,
            server_default="scheduled",
        ),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_post_id", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["generated_content_id"], ["generated_contents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["idea_id"], ["ideas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_scheduled_publications_user_id",
        "scheduled_publications",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_scheduled_publications_idea_id",
        "scheduled_publications",
        ["idea_id"],
        unique=False,
    )
    op.create_index(
        "ix_scheduled_publications_generated_content_id",
        "scheduled_publications",
        ["generated_content_id"],
        unique=False,
    )
    op.create_index(
        "ix_scheduled_publications_scheduled_at",
        "scheduled_publications",
        ["scheduled_at"],
        unique=False,
    )
    op.create_index(
        "ix_scheduled_publications_status",
        "scheduled_publications",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_scheduled_publications_status_scheduled_at",
        "scheduled_publications",
        ["status", "scheduled_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_scheduled_publications_status_scheduled_at", table_name="scheduled_publications")
    op.drop_index("ix_scheduled_publications_status", table_name="scheduled_publications")
    op.drop_index("ix_scheduled_publications_scheduled_at", table_name="scheduled_publications")
    op.drop_index("ix_scheduled_publications_generated_content_id", table_name="scheduled_publications")
    op.drop_index("ix_scheduled_publications_idea_id", table_name="scheduled_publications")
    op.drop_index("ix_scheduled_publications_user_id", table_name="scheduled_publications")
    op.drop_table("scheduled_publications")
