"""user_social_connections: one Meta + one LinkedIn per idea (not per user)

Revision ID: s1t2u3v4w5x6
Revises: r0s1t2u3v4w5
Create Date: 2026-05-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision: str = "s1t2u3v4w5x6"
down_revision: Union[str, Sequence[str], None] = "r0s1t2u3v4w5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "user_social_connections" not in insp.get_table_names():
        return

    cols = {c["name"] for c in insp.get_columns("user_social_connections")}
    if "idea_id" in cols:
        return

    op.drop_constraint("uq_user_social_provider", "user_social_connections", type_="unique")

    op.add_column(
        "user_social_connections",
        sa.Column("idea_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_user_social_connections_idea_id",
        "user_social_connections",
        ["idea_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_user_social_connections_idea_id",
        "user_social_connections",
        "ideas",
        ["idea_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Rattacher chaque ligne existante à la dernière idée du même utilisateur.
    bind.execute(
        text(
            """
            UPDATE user_social_connections u
            SET idea_id = (
                SELECT i.id FROM ideas i
                WHERE i.user_id = u.user_id
                ORDER BY i.created_at DESC NULLS LAST, i.id DESC
                LIMIT 1
            )
            WHERE EXISTS (SELECT 1 FROM ideas i2 WHERE i2.user_id = u.user_id)
            """
        )
    )
    # Utilisateurs sans idée : supprimer les jetons orphelins.
    bind.execute(text("DELETE FROM user_social_connections WHERE idea_id IS NULL"))

    # Dupliquer les connexions sur les autres idées du même user (même payload).
    bind.execute(
        text(
            """
            INSERT INTO user_social_connections (
                user_id, idea_id, provider, payload_encrypted,
                account_name, page_name, facebook_url, instagram_url, linkedin_url,
                created_at, updated_at
            )
            SELECT
                u.user_id,
                i.id,
                u.provider,
                u.payload_encrypted,
                u.account_name,
                u.page_name,
                u.facebook_url,
                u.instagram_url,
                u.linkedin_url,
                u.created_at,
                u.updated_at
            FROM ideas i
            INNER JOIN user_social_connections u ON u.user_id = i.user_id
            WHERE u.idea_id IS NOT NULL
              AND i.id <> u.idea_id
              AND NOT EXISTS (
                SELECT 1 FROM user_social_connections x
                WHERE x.idea_id = i.id AND x.provider = u.provider
              )
            """
        )
    )

    op.alter_column(
        "user_social_connections",
        "idea_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.create_unique_constraint(
        "uq_idea_social_provider",
        "user_social_connections",
        ["idea_id", "provider"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "user_social_connections" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("user_social_connections")}
    if "idea_id" not in cols:
        return

    op.drop_constraint("uq_idea_social_provider", "user_social_connections", type_="unique")

    # Une ligne par (user_id, provider) : garder la plus petite id.
    bind.execute(
        text(
            """
            DELETE FROM user_social_connections a
            WHERE a.id NOT IN (
                SELECT MIN(id) FROM user_social_connections GROUP BY user_id, provider
            )
            """
        )
    )

    op.drop_constraint("fk_user_social_connections_idea_id", "user_social_connections", type_="foreignkey")
    op.drop_index("ix_user_social_connections_idea_id", table_name="user_social_connections")
    op.drop_column("user_social_connections", "idea_id")

    op.create_unique_constraint(
        "uq_user_social_provider",
        "user_social_connections",
        ["user_id", "provider"],
    )
