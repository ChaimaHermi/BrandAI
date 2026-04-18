"""create generated_contents table for social content traceability

Revision ID: k3l4m5n6o7p8
Revises: j2k3l4m5n6o7
Create Date: 2026-04-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "k3l4m5n6o7p8"
down_revision: Union[str, Sequence[str], None] = "j2k3l4m5n6o7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "generated_contents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("idea_id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("char_count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="generated"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("publish_error", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["idea_id"], ["ideas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_generated_contents_idea_id"),
        "generated_contents",
        ["idea_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_generated_contents_status"),
        "generated_contents",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_generated_contents_status"), table_name="generated_contents")
    op.drop_index(op.f("ix_generated_contents_idea_id"), table_name="generated_contents")
    op.drop_table("generated_contents")
