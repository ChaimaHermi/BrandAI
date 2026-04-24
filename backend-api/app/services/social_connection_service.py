from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.social_token_crypto import decrypt_json_payload, encrypt_json_payload
from app.models.user_social_connection import UserSocialConnection
from app.schemas.social_connection import (
    LinkedInConnectionOut,
    MetaConnectionOut,
    MetaPageOut,
    SocialConnectionsOut,
)


PROVIDER_META = "meta"
PROVIDER_LINKEDIN = "linkedin"


def _row(db: Session, user_id: int, provider: str) -> UserSocialConnection | None:
    return (
        db.query(UserSocialConnection)
        .filter(
            UserSocialConnection.user_id == user_id,
            UserSocialConnection.provider == provider,
        )
        .first()
    )


def get_connections_for_user(db: Session, user_id: int) -> SocialConnectionsOut:
    meta_out = None
    li_out = None
    mr = _row(db, user_id, PROVIDER_META)
    if mr:
        data = decrypt_json_payload(mr.payload_encrypted)
        pages_raw = data.get("pages") or []
        pages = [
            MetaPageOut(
                id=str(p.get("id")),
                name=p.get("name"),
                access_token=str(p.get("access_token") or ""),
            )
            for p in pages_raw
            if p.get("id") and p.get("access_token")
        ]
        meta_out = MetaConnectionOut(
            user_access_token=str(data.get("user_access_token") or ""),
            pages=pages,
            selected_page_id=data.get("selected_page_id"),
        )
    lr = _row(db, user_id, PROVIDER_LINKEDIN)
    if lr:
        data = decrypt_json_payload(lr.payload_encrypted)
        li_out = LinkedInConnectionOut(
            access_token=str(data.get("access_token") or ""),
            person_urn=str(data.get("person_urn") or ""),
            name=data.get("name"),
        )
    return SocialConnectionsOut(meta=meta_out, linkedin=li_out)


def upsert_meta(
    db: Session,
    *,
    user_id: int,
    user_access_token: str,
    pages: list[dict[str, Any]],
    selected_page_id: str | None,
) -> None:
    payload = {
        "user_access_token": user_access_token.strip(),
        "pages": pages,
        "selected_page_id": (selected_page_id or "").strip() or None,
    }
    enc = encrypt_json_payload(payload)
    row = _row(db, user_id, PROVIDER_META)
    if row:
        row.payload_encrypted = enc
    else:
        db.add(
            UserSocialConnection(
                user_id=user_id,
                provider=PROVIDER_META,
                payload_encrypted=enc,
            )
        )
    db.commit()


def patch_meta_selected_page(db: Session, *, user_id: int, selected_page_id: str) -> bool:
    row = _row(db, user_id, PROVIDER_META)
    if not row:
        return False
    data = decrypt_json_payload(row.payload_encrypted)
    page_ids = {str(p.get("id")) for p in (data.get("pages") or [])}
    sid = selected_page_id.strip()
    if sid not in page_ids:
        return False
    data["selected_page_id"] = sid
    row.payload_encrypted = encrypt_json_payload(data)
    db.commit()
    return True


def upsert_linkedin(
    db: Session,
    *,
    user_id: int,
    access_token: str,
    person_urn: str,
    name: str | None,
) -> None:
    payload = {
        "access_token": access_token.strip(),
        "person_urn": person_urn.strip(),
        "name": name,
    }
    enc = encrypt_json_payload(payload)
    row = _row(db, user_id, PROVIDER_LINKEDIN)
    if row:
        row.payload_encrypted = enc
    else:
        db.add(
            UserSocialConnection(
                user_id=user_id,
                provider=PROVIDER_LINKEDIN,
                payload_encrypted=enc,
            )
        )
    db.commit()


def delete_meta(db: Session, *, user_id: int) -> bool:
    row = _row(db, user_id, PROVIDER_META)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def delete_linkedin(db: Session, *, user_id: int) -> bool:
    row = _row(db, user_id, PROVIDER_LINKEDIN)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True
