"""create branding results tables and brand_kits

Revision ID: j2k3l4m5n6o7
Revises: i0j1k2l3m4n5
Create Date: 2026-04-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision: str = "j2k3l4m5n6o7"
down_revision: Union[str, Sequence[str], None] = "i0j1k2l3m4n5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_names(bind) -> set[str]:
    return set(inspect(bind).get_table_names())


def upgrade() -> None:
    bind = op.get_bind()
    tables = _table_names(bind)

    if "naming_results" not in tables:
        op.create_table(
            "naming_results",
            sa.Column("id", UUID(as_uuid=True), nullable=False),
            sa.Column("idea_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
            sa.Column("preferences", JSONB(), nullable=True),
            sa.Column("generated", JSONB(), nullable=True),
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
            sa.Column("chosen_name", sa.Text(), nullable=True),
            sa.Column("chosen_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["idea_id"], ["ideas.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("idea_id", name="uq_naming_results_idea_id"),
        )

    if "slogan_results" not in tables:
        op.create_table(
            "slogan_results",
            sa.Column("id", UUID(as_uuid=True), nullable=False),
            sa.Column("idea_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
            sa.Column("preferences", JSONB(), nullable=True),
            sa.Column("generated", JSONB(), nullable=True),
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
            sa.Column("chosen_slogan", sa.Text(), nullable=True),
            sa.Column("based_on_name", sa.Text(), nullable=True),
            sa.Column("chosen_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["idea_id"], ["ideas.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("idea_id", name="uq_slogan_results_idea_id"),
        )

    if "palette_results" not in tables:
        op.create_table(
            "palette_results",
            sa.Column("id", UUID(as_uuid=True), nullable=False),
            sa.Column("idea_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
            sa.Column("preferences", JSONB(), nullable=True),
            sa.Column("generated", JSONB(), nullable=True),
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
            sa.Column("chosen", JSONB(), nullable=True),
            sa.Column("chosen_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["idea_id"], ["ideas.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("idea_id", name="uq_palette_results_idea_id"),
        )

    if "logo_results" not in tables:
        op.create_table(
            "logo_results",
            sa.Column("id", UUID(as_uuid=True), nullable=False),
            sa.Column("idea_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
            sa.Column("preferences", JSONB(), nullable=True),
            sa.Column("generated", JSONB(), nullable=True),
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
            sa.Column("style", sa.Text(), nullable=True),
            sa.Column("logo_type", sa.Text(), nullable=True),
            sa.Column("svg_data", sa.Text(), nullable=True),
            sa.Column("variants", JSONB(), nullable=True),
            sa.Column("chosen", JSONB(), nullable=True),
            sa.Column("chosen_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["idea_id"], ["ideas.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("idea_id", name="uq_logo_results_idea_id"),
        )

    tables = _table_names(bind)
    if "brand_kits" not in tables:
        op.create_table(
            "brand_kits",
            sa.Column("id", UUID(as_uuid=True), nullable=False),
            sa.Column("idea_id", sa.Integer(), nullable=False),
            sa.Column("naming_id", UUID(as_uuid=True), nullable=True),
            sa.Column("slogan_id", UUID(as_uuid=True), nullable=True),
            sa.Column("palette_id", UUID(as_uuid=True), nullable=True),
            sa.Column("logo_id", UUID(as_uuid=True), nullable=True),
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
            sa.ForeignKeyConstraint(["naming_id"], ["naming_results.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["slogan_id"], ["slogan_results.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["palette_id"], ["palette_results.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["logo_id"], ["logo_results.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("idea_id", name="uq_brand_kits_idea_id"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    tables = _table_names(bind)

    if "brand_kits" in tables:
        op.drop_table("brand_kits")
    if "logo_results" in tables:
        op.drop_table("logo_results")
    if "palette_results" in tables:
        op.drop_table("palette_results")
    if "slogan_results" in tables:
        op.drop_table("slogan_results")
    if "naming_results" in tables:
        op.drop_table("naming_results")
