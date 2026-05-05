"""create social ETL tables

Revision ID: u2v3w4x5y6z7
Revises: t1u2v3w4x5y6
Create Date: 2026-05-05
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "u2v3w4x5y6z7"
down_revision: Union[str, Sequence[str], None] = "t1u2v3w4x5y6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "social_posts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("connection_id", sa.Integer(), nullable=False),
        sa.Column("post_external_id", sa.String(length=100), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("media_type", sa.String(length=20), nullable=True),
        sa.Column("media_url", sa.Text(), nullable=True),
        sa.Column("permalink_url", sa.Text(), nullable=True),
        sa.Column("likes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("comments", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("shares", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("saves", sa.Integer(), nullable=True),
        sa.Column("clicks", sa.Integer(), nullable=True),
        sa.Column("reach", sa.Integer(), nullable=True),
        sa.Column("impressions", sa.Integer(), nullable=True),
        sa.Column("video_views", sa.Integer(), nullable=True),
        sa.Column("reactions_like", sa.Integer(), nullable=True),
        sa.Column("reactions_love", sa.Integer(), nullable=True),
        sa.Column("reactions_haha", sa.Integer(), nullable=True),
        sa.Column("reactions_wow", sa.Integer(), nullable=True),
        sa.Column("reactions_sad", sa.Integer(), nullable=True),
        sa.Column("reactions_angry", sa.Integer(), nullable=True),
        sa.Column(
            "reactions_breakdown",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["connection_id"],
            ["social_connections.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("post_external_id", name="uq_social_posts_post_external_id"),
    )
    op.create_index(
        "ix_social_posts_connection_id",
        "social_posts",
        ["connection_id"],
        unique=False,
    )
    op.create_index(
        "ix_social_posts_published_at",
        "social_posts",
        ["published_at"],
        unique=False,
    )
    op.create_index(
        "ix_social_posts_post_external_id",
        "social_posts",
        ["post_external_id"],
        unique=True,
    )

    op.create_table(
        "social_daily_insights",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("connection_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("followers_count", sa.Integer(), nullable=True),
        sa.Column("reach", sa.Integer(), nullable=True),
        sa.Column("impressions", sa.Integer(), nullable=True),
        sa.Column("post_engagements", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["connection_id"],
            ["social_connections.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "connection_id",
            "date",
            name="uq_social_daily_insights_connection_date",
        ),
    )

    op.create_table(
        "sync_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("connection_id", sa.Integer(), nullable=True),
        sa.Column("sync_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sync_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("posts_fetched", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["connection_id"],
            ["social_connections.id"],
            ondelete="SET NULL",
        ),
    )
    op.create_index(
        "ix_sync_logs_connection_id",
        "sync_logs",
        ["connection_id"],
        unique=False,
    )
    op.create_index(
        "ix_sync_logs_sync_start",
        "sync_logs",
        ["sync_start"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_sync_logs_sync_start", table_name="sync_logs")
    op.drop_index("ix_sync_logs_connection_id", table_name="sync_logs")
    op.drop_table("sync_logs")
    op.drop_table("social_daily_insights")
    op.drop_index("ix_social_posts_post_external_id", table_name="social_posts")
    op.drop_index("ix_social_posts_published_at", table_name="social_posts")
    op.drop_index("ix_social_posts_connection_id", table_name="social_posts")
    op.drop_table("social_posts")
