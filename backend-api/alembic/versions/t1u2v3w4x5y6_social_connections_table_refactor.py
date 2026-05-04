"""Rename user_social_connections to social_connections; platform rows; migrate data.

Revision ID: t1u2v3w4x5y6
Revises: s1t2u3v4w5x6
Create Date: 2026-05-04

"""

from __future__ import annotations

from typing import Any, Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision: str = "t1u2v3w4x5y6"
down_revision: Union[str, Sequence[str], None] = "s1t2u3v4w5x6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "social_connections" in insp.get_table_names():
        return

    op.create_table(
        "social_connections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("idea_id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(length=64), nullable=False),
        sa.Column("platform_account_id", sa.String(length=255), nullable=True),
        sa.Column("profile_url", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("account_name", sa.String(length=255), nullable=True),
        sa.Column("page_name", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["idea_id"], ["ideas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idea_id", "platform", name="uq_social_idea_platform"),
    )
    op.create_index("ix_social_connections_user_id", "social_connections", ["user_id"], unique=False)
    op.create_index("ix_social_connections_idea_id", "social_connections", ["idea_id"], unique=False)
    op.create_index("ix_social_connections_platform", "social_connections", ["platform"], unique=False)

    insp = sa.inspect(bind)
    if "user_social_connections" not in insp.get_table_names():
        return

    from app.core.social_token_crypto import decrypt_json_payload, encrypt_json_payload

    res = bind.execute(
        text(
            """
            SELECT user_id, idea_id, provider, payload_encrypted,
                   account_name, page_name, facebook_url, instagram_url, linkedin_url,
                   created_at, updated_at
            FROM user_social_connections
            ORDER BY id
            """
        )
    )
    rows = res.fetchall()

    def ins(
        *,
        user_id: int,
        idea_id: int,
        platform: str,
        access_token_encrypted: str,
        platform_account_id: str | None,
        profile_url: str | None,
        token_expires_at: Any,
        account_name: str | None,
        page_name: str | None,
        created_at: Any,
        updated_at: Any,
    ) -> None:
        bind.execute(
            text(
                """
                INSERT INTO social_connections (
                    user_id, idea_id, platform, platform_account_id, profile_url, token_expires_at,
                    access_token_encrypted, account_name, page_name, created_at, updated_at
                ) VALUES (
                    :user_id, :idea_id, :platform, :platform_account_id, :profile_url, :token_expires_at,
                    :access_token_encrypted, :account_name, :page_name, :created_at, :updated_at
                )
                """
            ),
            {
                "user_id": user_id,
                "idea_id": idea_id,
                "platform": platform,
                "platform_account_id": platform_account_id,
                "profile_url": profile_url,
                "token_expires_at": token_expires_at,
                "access_token_encrypted": access_token_encrypted,
                "account_name": account_name,
                "page_name": page_name,
                "created_at": created_at,
                "updated_at": updated_at,
            },
        )

    for row in rows:
        (
            user_id,
            idea_id,
            provider,
            payload_enc,
            account_name,
            page_name,
            facebook_url,
            instagram_url,
            linkedin_url,
            created_at,
            updated_at,
        ) = row
        provider = (provider or "").strip().lower()
        if provider == "linkedin":
            li_acct = None
            try:
                data = decrypt_json_payload(payload_enc)
                urn = (data.get("person_urn") or "").strip()
                if urn.startswith("urn:li:person:"):
                    li_acct = urn.replace("urn:li:person:", "")[:255] or None
            except Exception:
                pass
            ins(
                user_id=user_id,
                idea_id=idea_id,
                platform="linkedin",
                access_token_encrypted=payload_enc,
                platform_account_id=li_acct,
                profile_url=(linkedin_url or "").strip() or None,
                token_expires_at=None,
                account_name=account_name,
                page_name=page_name,
                created_at=created_at,
                updated_at=updated_at,
            )
            continue

        if provider != "meta":
            continue

        data: dict[str, Any] = {}
        try:
            data = decrypt_json_payload(payload_enc)
        except Exception:
            data = {}
        pages_raw = data.get("pages") or []
        pages = [p for p in pages_raw if p.get("id") and p.get("access_token")]
        sid = (data.get("selected_page_id") or "").strip() or None
        page = None
        if sid:
            page = next((p for p in pages if str(p.get("id")) == str(sid)), None)
        if not page and len(pages) == 1:
            page = pages[0]
        page_id_str = str(page.get("id")).strip() if page else None
        page_tok = str(page.get("access_token") or "").strip() if page else None

        ins(
            user_id=user_id,
            idea_id=idea_id,
            platform="facebook_page",
            access_token_encrypted=payload_enc,
            platform_account_id=page_id_str,
            profile_url=(facebook_url or "").strip() or None,
            token_expires_at=None,
            account_name=account_name,
            page_name=page_name,
            created_at=created_at,
            updated_at=updated_at,
        )

        ig_url = (instagram_url or "").strip() or None
        if ig_url and page_id_str and page_tok:
            ig_payload = {
                "page_id": page_id_str,
                "page_access_token": page_tok,
            }
            ig_username = None
            if "instagram.com/" in ig_url.lower():
                try:
                    tail = ig_url.lower().split("instagram.com/", 1)[1]
                    tail = tail.split("?", 1)[0].strip("/").split("/", 1)[0]
                    ig_username = tail or None
                except Exception:
                    ig_username = None
            ins(
                user_id=user_id,
                idea_id=idea_id,
                platform="instagram_business",
                access_token_encrypted=encrypt_json_payload(ig_payload),
                platform_account_id=(ig_username or page_id_str)[:255],
                profile_url=ig_url,
                token_expires_at=None,
                account_name=ig_username,
                page_name=page_name,
                created_at=created_at,
                updated_at=updated_at,
            )

    op.drop_table("user_social_connections")


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "social_connections" not in insp.get_table_names():
        return
    if "user_social_connections" in insp.get_table_names():
        op.drop_table("user_social_connections")

    op.create_table(
        "user_social_connections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("idea_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("payload_encrypted", sa.Text(), nullable=False),
        sa.Column("account_name", sa.String(length=255), nullable=True),
        sa.Column("page_name", sa.String(length=512), nullable=True),
        sa.Column("facebook_url", sa.String(length=1024), nullable=True),
        sa.Column("instagram_url", sa.String(length=1024), nullable=True),
        sa.Column("linkedin_url", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["idea_id"], ["ideas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idea_id", "provider", name="uq_idea_social_provider"),
    )
    op.create_index("ix_user_social_connections_user_id", "user_social_connections", ["user_id"], unique=False)
    op.create_index("ix_user_social_connections_idea_id", "user_social_connections", ["idea_id"], unique=False)
    op.create_index("ix_user_social_connections_provider", "user_social_connections", ["provider"], unique=False)

    res = bind.execute(
        text(
            """
            SELECT user_id, idea_id, platform, access_token_encrypted,
                   account_name, page_name, platform_account_id, profile_url,
                   created_at, updated_at
            FROM social_connections
            ORDER BY idea_id,
              CASE platform
                WHEN 'linkedin' THEN 1
                WHEN 'facebook_page' THEN 2
                WHEN 'instagram_business' THEN 3
                ELSE 4
              END,
              id
            """
        )
    )
    for row in res.fetchall():
        (
            user_id,
            idea_id,
            platform,
            access_enc,
            account_name,
            page_name,
            platform_account_id,
            profile_url,
            created_at,
            updated_at,
        ) = row
        plat = (platform or "").strip()
        if plat == "linkedin":
            bind.execute(
                text(
                    """
                    INSERT INTO user_social_connections (
                        user_id, idea_id, provider, payload_encrypted,
                        account_name, page_name, facebook_url, instagram_url, linkedin_url,
                        created_at, updated_at
                    ) VALUES (
                        :user_id, :idea_id, 'linkedin', :payload_encrypted,
                        :account_name, :page_name, NULL, NULL, :linkedin_url,
                        :created_at, :updated_at
                    )
                    """
                ),
                {
                    "user_id": user_id,
                    "idea_id": idea_id,
                    "payload_encrypted": access_enc,
                    "account_name": account_name,
                    "page_name": page_name,
                    "linkedin_url": profile_url,
                    "created_at": created_at,
                    "updated_at": updated_at,
                },
            )
        elif plat == "facebook_page":
            bind.execute(
                text(
                    """
                    INSERT INTO user_social_connections (
                        user_id, idea_id, provider, payload_encrypted,
                        account_name, page_name, facebook_url, instagram_url, linkedin_url,
                        created_at, updated_at
                    ) VALUES (
                        :user_id, :idea_id, 'meta', :payload_encrypted,
                        :account_name, :page_name, :facebook_url, NULL, NULL,
                        :created_at, :updated_at
                    )
                    """
                ),
                {
                    "user_id": user_id,
                    "idea_id": idea_id,
                    "payload_encrypted": access_enc,
                    "account_name": account_name,
                    "page_name": page_name,
                    "facebook_url": profile_url,
                    "created_at": created_at,
                    "updated_at": updated_at,
                },
            )
        elif plat == "instagram_business":
            bind.execute(
                text(
                    """
                    UPDATE user_social_connections
                    SET instagram_url = :ig_url,
                        updated_at = :updated_at
                    WHERE idea_id = :idea_id AND provider = 'meta'
                    """
                ),
                {"ig_url": profile_url, "updated_at": updated_at, "idea_id": idea_id},
            )

    op.drop_table("social_connections")
