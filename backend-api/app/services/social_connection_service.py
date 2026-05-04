"""Connexions OAuth Meta / LinkedIn : persistance, lecture, enrichissement public (nom, pseudo, URL)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.social_token_crypto import decrypt_json_payload, encrypt_json_payload
from app.models.idea import Idea
from app.models.user_social_connection import UserSocialConnection
from app.schemas.social_connection import (
    LinkedInConnectionOut,
    MetaConnectionOut,
    MetaPageOut,
    SocialConnectionsOut,
)

logger = logging.getLogger(__name__)

PROVIDER_META = "meta"
PROVIDER_LINKEDIN = "linkedin"

_GRAPH_BASE = f"https://graph.facebook.com/{settings.META_GRAPH_API_VERSION.strip()}"

# Ancien emplacement de l’URL manuelle (JSON chiffré) — lecture seule tant que des lignes existent.
_LEGACY_LINKEDIN_URL_JSON_KEY = "manual_profile_url"


def _legacy_linkedin_url_from_payload(data: dict[str, Any]) -> str | None:
    return _strip_or_none(data.get(_LEGACY_LINKEDIN_URL_JSON_KEY))


def _payload_without_legacy_linkedin_manual(data: dict[str, Any]) -> dict[str, Any] | None:
    if _LEGACY_LINKEDIN_URL_JSON_KEY not in data:
        return None
    out = {k: v for k, v in data.items() if k != _LEGACY_LINKEDIN_URL_JSON_KEY}
    return out


@dataclass(frozen=True)
class _PublicAccountTrace:
    account_name: str | None
    page_name: str | None
    facebook_url: str | None = None
    instagram_url: str | None = None
    linkedin_url: str | None = None


def _strip_or_none(s: str | None) -> str | None:
    if s is None:
        return None
    t = str(s).strip()
    return t or None


def _facebook_page_url(
    page_id: str,
    *,
    link: str | None,
    page_username: str | None,
) -> str | None:
    if link:
        return link
    if page_username:
        return f"https://www.facebook.com/{page_username}/"
    return f"https://www.facebook.com/{page_id}"


def _deep_find_linkedin_in_url(obj: Any) -> str | None:
    """Repère une URL publique /in/… dans une réponse JSON LinkedIn (userinfo, etc.)."""
    if isinstance(obj, str):
        low = obj.lower()
        if "linkedin.com/in/" in low and "linkedin.com/in/me" not in low:
            s = obj.strip().strip('"').split(",")[0].strip()
            if s.startswith("http"):
                return s
        return None
    if isinstance(obj, dict):
        for v in obj.values():
            u = _deep_find_linkedin_in_url(v)
            if u:
                return u
    if isinstance(obj, list):
        for v in obj:
            u = _deep_find_linkedin_in_url(v)
            if u:
                return u
    return None


def _vanity_from_linkedin_in_url(url: str | None) -> str | None:
    if not url or "linkedin.com/in/" not in url.lower():
        return None
    try:
        tail = url.lower().split("linkedin.com/in/", 1)[1]
        tail = tail.split("?", 1)[0].split("/", 1)[0].strip().strip("/")
        return tail or None
    except Exception:
        return None


def _fetch_meta_public_trace(page_id: str, page_access_token: str) -> _PublicAccountTrace:
    """Page Meta : URLs Facebook + Instagram (compte pro lié) et champs d’affichage."""
    token = (page_access_token or "").strip()
    if not token or not str(page_id).strip():
        return _PublicAccountTrace(None, None)

    fields = "name,username,link,instagram_business_account{username,name}"
    params: dict[str, Any] = {"fields": fields, "access_token": token}
    url = f"{_GRAPH_BASE}/{page_id.lstrip('/')}"
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.get(url, params=params)
            data = r.json() if r.content else {}
            if r.status_code != 200:
                err = data.get("error") if isinstance(data, dict) else data
                logger.warning("Meta Graph page %s: %s", page_id, err)
                return _PublicAccountTrace(None, None)
    except Exception as e:
        logger.warning("Meta Graph request failed: %s", e)
        return _PublicAccountTrace(None, None)

    if not isinstance(data, dict):
        return _PublicAccountTrace(None, None)

    page_name_fb = _strip_or_none(data.get("name"))
    page_username = _strip_or_none(data.get("username"))
    link = _strip_or_none(data.get("link"))
    fb_url = _strip_or_none(_facebook_page_url(str(page_id), link=link, page_username=page_username))

    ig = data.get("instagram_business_account")
    if isinstance(ig, dict):
        ig_user = _strip_or_none(ig.get("username"))
        ig_name = _strip_or_none(ig.get("name"))
        if ig_user:
            ig_url = f"https://www.instagram.com/{ig_user}/"
            return _PublicAccountTrace(
                account_name=ig_user,
                page_name=ig_name or page_name_fb,
                facebook_url=fb_url,
                instagram_url=ig_url,
            )

    account = page_username or str(page_id)
    return _PublicAccountTrace(
        account_name=_strip_or_none(account),
        page_name=page_name_fb,
        facebook_url=fb_url,
        instagram_url=None,
    )


def _linkedin_userinfo_fallback(
    client: httpx.Client,
    token: str,
    fallback_display_name: str | None,
) -> _PublicAccountTrace:
    try:
        r = client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = r.json() if r.content else {}
        if r.status_code != 200:
            logger.warning("LinkedIn userinfo: %s", data)
            return _PublicAccountTrace(None, _strip_or_none(fallback_display_name))
    except Exception as e:
        logger.warning("LinkedIn userinfo failed: %s", e)
        return _PublicAccountTrace(None, _strip_or_none(fallback_display_name))

    if not isinstance(data, dict):
        return _PublicAccountTrace(None, _strip_or_none(fallback_display_name))

    name = _strip_or_none(data.get("name")) or _strip_or_none(fallback_display_name)
    sub = _strip_or_none(data.get("sub"))
    in_url = _deep_find_linkedin_in_url(data)
    return _PublicAccountTrace(
        account_name=sub,
        page_name=name,
        linkedin_url=in_url,
    )


def _fetch_linkedin_public_trace(
    access_token: str,
    fallback_display_name: str | None,
    person_urn: str | None = None,
) -> _PublicAccountTrace:
    token = (access_token or "").strip()
    if not token:
        return _PublicAccountTrace(None, None)

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.get(
                "https://api.linkedin.com/v2/me",
                params={
                    "projection": "(id,localizedFirstName,localizedLastName,vanityName)",
                },
                headers=headers,
            )
            data = r.json() if r.content else {}
            if r.status_code != 200:
                logger.warning("LinkedIn v2/me: %s", data)
                return _linkedin_userinfo_fallback(client, token, fallback_display_name)

            if not isinstance(data, dict):
                return _linkedin_userinfo_fallback(client, token, fallback_display_name)

            first = _strip_or_none(data.get("localizedFirstName")) or ""
            last = _strip_or_none(data.get("localizedLastName")) or ""
            display = _strip_or_none(fallback_display_name) or (
                f"{first} {last}".strip() or None
            )
            vanity = _strip_or_none(data.get("vanityName"))
            if vanity:
                li_url = f"https://www.linkedin.com/in/{vanity}/"
                return _PublicAccountTrace(
                    account_name=vanity,
                    page_name=display,
                    linkedin_url=li_url,
                )

            in_url = _deep_find_linkedin_in_url(data)
            ui_json: dict[str, Any] = {}
            if not in_url:
                try:
                    ur = client.get(
                        "https://api.linkedin.com/v2/userinfo",
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    raw_ui = ur.json() if ur.content else {}
                    ui_json = raw_ui if isinstance(raw_ui, dict) else {}
                    if ur.status_code != 200:
                        ui_json = {}
                except Exception:
                    ui_json = {}
                in_url = _deep_find_linkedin_in_url(data) or _deep_find_linkedin_in_url(ui_json)

            sub = data.get("id")
            sid = _strip_or_none(str(sub)) if sub is not None else None
            urn_tail = _strip_or_none((person_urn or "").replace("urn:li:person:", ""))
            vanity_from_url = _vanity_from_linkedin_in_url(in_url)
            account = vanity_from_url or sid or urn_tail
            return _PublicAccountTrace(
                account_name=account,
                page_name=display,
                linkedin_url=_strip_or_none(in_url),
            )
    except Exception as e:
        logger.warning("LinkedIn v2/me request failed: %s", e)
        return _PublicAccountTrace(None, _strip_or_none(fallback_display_name))


def _row(db: Session, idea_id: int, provider: str) -> UserSocialConnection | None:
    return (
        db.query(UserSocialConnection)
        .filter(
            UserSocialConnection.idea_id == idea_id,
            UserSocialConnection.provider == provider,
        )
        .first()
    )


def _assert_idea_owned(db: Session, idea_id: int, user_id: int) -> None:
    ok = (
        db.query(Idea.id)
        .filter(Idea.id == idea_id, Idea.user_id == user_id)
        .first()
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idée introuvable ou accès refusé.",
        )


def get_connections_for_idea(db: Session, idea_id: int, user_id: int) -> SocialConnectionsOut:
    _assert_idea_owned(db, idea_id, user_id)
    meta_out = None
    li_out = None
    mr = _row(db, idea_id, PROVIDER_META)
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
            account_name=mr.account_name,
            page_name=mr.page_name,
            facebook_url=mr.facebook_url,
            instagram_url=mr.instagram_url,
        )
    lr = _row(db, idea_id, PROVIDER_LINKEDIN)
    if lr:
        data = decrypt_json_payload(lr.payload_encrypted)
        col_url = _strip_or_none(lr.linkedin_url)
        li_out = LinkedInConnectionOut(
            access_token=str(data.get("access_token") or ""),
            person_urn=str(data.get("person_urn") or ""),
            name=data.get("name"),
            account_name=lr.account_name,
            page_name=lr.page_name,
            linkedin_url=col_url or _legacy_linkedin_url_from_payload(data),
        )
    return SocialConnectionsOut(meta=meta_out, linkedin=li_out)


def _trace_meta_row(
    row: UserSocialConnection,
    *,
    pages: list[dict[str, Any]],
    selected_page_id: str | None,
) -> None:
    sid = (selected_page_id or "").strip() or None
    page = None
    if sid:
        page = next((p for p in pages if str(p.get("id")) == str(sid)), None)
    if not page and len(pages) == 1:
        page = pages[0]
    if not page:
        return
    pid = str(page.get("id") or "").strip()
    tok = str(page.get("access_token") or "").strip()
    if not pid or not tok:
        return
    t = _fetch_meta_public_trace(pid, tok)
    row.account_name = t.account_name
    row.page_name = t.page_name
    row.facebook_url = t.facebook_url
    row.instagram_url = t.instagram_url


def upsert_meta(
    db: Session,
    *,
    idea_id: int,
    user_id: int,
    user_access_token: str,
    pages: list[dict[str, Any]],
    selected_page_id: str | None,
) -> None:
    _assert_idea_owned(db, idea_id, user_id)
    payload = {
        "user_access_token": user_access_token.strip(),
        "pages": pages,
        "selected_page_id": (selected_page_id or "").strip() or None,
    }
    enc = encrypt_json_payload(payload)
    row = _row(db, idea_id, PROVIDER_META)
    if row:
        row.payload_encrypted = enc
    else:
        row = UserSocialConnection(
            user_id=user_id,
            idea_id=idea_id,
            provider=PROVIDER_META,
            payload_encrypted=enc,
        )
        db.add(row)
    _trace_meta_row(
        row,
        pages=pages,
        selected_page_id=payload["selected_page_id"],
    )
    db.commit()


def patch_meta_selected_page(db: Session, *, idea_id: int, user_id: int, selected_page_id: str) -> bool:
    _assert_idea_owned(db, idea_id, user_id)
    row = _row(db, idea_id, PROVIDER_META)
    if not row:
        return False
    data = decrypt_json_payload(row.payload_encrypted)
    page_ids = {str(p.get("id")) for p in (data.get("pages") or [])}
    sid = selected_page_id.strip()
    if sid not in page_ids:
        return False
    data["selected_page_id"] = sid
    row.payload_encrypted = encrypt_json_payload(data)
    _trace_meta_row(row, pages=list(data.get("pages") or []), selected_page_id=sid)
    db.commit()
    return True


def upsert_linkedin(
    db: Session,
    *,
    idea_id: int,
    user_id: int,
    access_token: str,
    person_urn: str,
    name: str | None,
) -> None:
    _assert_idea_owned(db, idea_id, user_id)
    row = _row(db, idea_id, PROVIDER_LINKEDIN)
    prev_li = _strip_or_none(row.linkedin_url) if row else None
    if row and not prev_li:
        try:
            prev_li = _legacy_linkedin_url_from_payload(
                decrypt_json_payload(row.payload_encrypted)
            )
        except Exception:
            pass
    payload: dict[str, Any] = {
        "access_token": access_token.strip(),
        "person_urn": person_urn.strip(),
        "name": name,
    }
    enc = encrypt_json_payload(payload)
    if row:
        row.payload_encrypted = enc
    else:
        row = UserSocialConnection(
            user_id=user_id,
            idea_id=idea_id,
            provider=PROVIDER_LINKEDIN,
            payload_encrypted=enc,
        )
        db.add(row)
    t = _fetch_linkedin_public_trace(
        payload["access_token"],
        name,
        payload.get("person_urn"),
    )
    row.account_name = t.account_name
    row.page_name = t.page_name
    row.linkedin_url = _strip_or_none(t.linkedin_url) or prev_li
    row.facebook_url = t.facebook_url
    row.instagram_url = t.instagram_url
    db.commit()


def patch_linkedin_url(
    db: Session,
    *,
    idea_id: int,
    user_id: int,
    linkedin_url: str | None,
) -> bool:
    _assert_idea_owned(db, idea_id, user_id)
    row = _row(db, idea_id, PROVIDER_LINKEDIN)
    if not row:
        return False
    row.linkedin_url = linkedin_url
    try:
        data = decrypt_json_payload(row.payload_encrypted)
        if isinstance(data, dict):
            cleaned = _payload_without_legacy_linkedin_manual(data)
            if cleaned is not None:
                row.payload_encrypted = encrypt_json_payload(cleaned)
    except Exception:
        pass
    db.commit()
    return True


def delete_meta(db: Session, *, idea_id: int, user_id: int) -> bool:
    _assert_idea_owned(db, idea_id, user_id)
    row = _row(db, idea_id, PROVIDER_META)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def delete_linkedin(db: Session, *, idea_id: int, user_id: int) -> bool:
    _assert_idea_owned(db, idea_id, user_id)
    row = _row(db, idea_id, PROVIDER_LINKEDIN)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True
