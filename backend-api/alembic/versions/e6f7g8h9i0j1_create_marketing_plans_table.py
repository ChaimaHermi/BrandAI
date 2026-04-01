"""create marketing_plans table

Revision ID: e6f7g8h9i0j1
Revises: d4e5f6g7h8i9
Create Date: 2026-04-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "e6f7g8h9i0j1"
down_revision: Union[str, Sequence[str], None] = "d4e5f6g7h8i9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "marketing_plans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("idea_id", sa.Integer(), nullable=True),
        sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["idea_id"], ["ideas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_marketing_plans_id"), "marketing_plans", ["id"], unique=False)
    op.create_index(op.f("ix_marketing_plans_idea_id"), "marketing_plans", ["idea_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_marketing_plans_idea_id"), table_name="marketing_plans")
    op.drop_index(op.f("ix_marketing_plans_id"), table_name="marketing_plans")
    op.drop_table("marketing_plans")
