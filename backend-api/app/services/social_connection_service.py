"""Connexions OAuth Meta / LinkedIn : persistance par plateforme, jetons chiffrés, métadonnées publiques."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.social_token_crypto import decrypt_json_payload, encrypt_json_payload
from app.models.idea import Idea
from app.models.social_connection import (
    PLATFORM_FACEBOOK_PAGE,
    PLATFORM_INSTAGRAM_BUSINESS,
    PLATFORM_LINKEDIN,
    SocialConnection,
)
from app.schemas.social_connection import (
    InstagramBusinessConnectionOut,
    LinkedInConnectionOut,
    MetaConnectionOut,
    MetaPageOut,
    SocialConnectionsOut,
)

logger = logging.getLogger(__name__)

_GRAPH_BASE = f"https://graph.facebook.com/{settings.META_GRAPH_API_VERSION.strip()}"

_LEGACY_LINKEDIN_URL_JSON_KEY = "manual_profile_url"


def _legacy_linkedin_url_from_payload(data: dict[str, Any]) -> str | None:
    return _strip_or_none(data.get(_LEGACY_LINKEDIN_URL_JSON_KEY))


def _payload_without_legacy_linkedin_manual(data: dict[str, Any]) -> dict[str, Any] | None:
    if _LEGACY_LINKEDIN_URL_JSON_KEY not in data:
        return None
    out = {k: v for k, v in data.items() if k != _LEGACY_LINKEDIN_URL_JSON_KEY}
    return out


@dataclass(frozen=True)
class _MetaGraphTrace:
    page_id: str
    facebook_profile_url: str | None
    page_display_name: str | None
    page_username: str | None
    ig_account_id: str | None
    ig_username: str | None
    ig_display_name: str | None
    ig_profile_url: str | None


@dataclass(frozen=True)
class _LinkedInPublicTrace:
    account_name: str | None
    page_name: str | None
    profile_url: str | None


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


def _fetch_meta_graph_trace(page_id: str, page_access_token: str) -> _MetaGraphTrace | None:
    token = (page_access_token or "").strip()
    pid = str(page_id).strip().lstrip("/")
    if not token or not pid:
        return None

    fields = "name,username,link,instagram_business_account{id,username,name}"
    params: dict[str, Any] = {"fields": fields, "access_token": token}
    url = f"{_GRAPH_BASE}/{pid}"
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.get(url, params=params)
            data = r.json() if r.content else {}
            if r.status_code != 200:
                err = data.get("error") if isinstance(data, dict) else data
                logger.warning("Meta Graph page %s: %s", pid, err)
                return None
    except Exception as e:
        logger.warning("Meta Graph request failed: %s", e)
        return None

    if not isinstance(data, dict):
        return None

    page_name_fb = _strip_or_none(data.get("name"))
    page_username = _strip_or_none(data.get("username"))
    link = _strip_or_none(data.get("link"))
    fb_url = _strip_or_none(_facebook_page_url(pid, link=link, page_username=page_username))

    ig_id = None
    ig_user = None
    ig_name = None
    ig_url = None
    ig = data.get("instagram_business_account")
    if isinstance(ig, dict):
        raw_id = ig.get("id")
        ig_id = _strip_or_none(str(raw_id)) if raw_id is not None else None
        ig_user = _strip_or_none(ig.get("username"))
        ig_name = _strip_or_none(ig.get("name"))
        if ig_user:
            ig_url = f"https://www.instagram.com/{ig_user}/"

    return _MetaGraphTrace(
        page_id=pid,
        facebook_profile_url=fb_url,
        page_display_name=page_name_fb,
        page_username=page_username,
        ig_account_id=ig_id,
        ig_username=ig_user,
        ig_display_name=ig_name,
        ig_profile_url=ig_url,
    )


def _linkedin_userinfo_fallback(
    client: httpx.Client,
    token: str,
    fallback_display_name: str | None,
) -> _LinkedInPublicTrace:
    try:
        r = client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = r.json() if r.content else {}
        if r.status_code != 200:
            logger.warning("LinkedIn userinfo: %s", data)
            return _LinkedInPublicTrace(None, _strip_or_none(fallback_display_name), None)
    except Exception as e:
        logger.warning("LinkedIn userinfo failed: %s", e)
        return _LinkedInPublicTrace(None, _strip_or_none(fallback_display_name), None)

    if not isinstance(data, dict):
        return _LinkedInPublicTrace(None, _strip_or_none(fallback_display_name), None)

    name = _strip_or_none(data.get("name")) or _strip_or_none(fallback_display_name)
    in_url = _deep_find_linkedin_in_url(data)
    return _LinkedInPublicTrace(
        account_name=_strip_or_none(data.get("sub")),
        page_name=name,
        profile_url=in_url,
    )


def _fetch_linkedin_public_trace(
    access_token: str,
    fallback_display_name: str | None,
    person_urn: str | None = None,
) -> _LinkedInPublicTrace:
    token = (access_token or "").strip()
    if not token:
        return _LinkedInPublicTrace(None, None, None)

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
                return _LinkedInPublicTrace(
                    account_name=vanity,
                    page_name=display,
                    profile_url=li_url,
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
            return _LinkedInPublicTrace(
                account_name=account,
                page_name=display,
                profile_url=_strip_or_none(in_url),
            )
    except Exception as e:
        logger.warning("LinkedIn v2/me request failed: %s", e)
        return _LinkedInPublicTrace(None, _strip_or_none(fallback_display_name), None)


def _row(db: Session, idea_id: int, platform: str) -> SocialConnection | None:
    return (
        db.query(SocialConnection)
        .filter(
            SocialConnection.idea_id == idea_id,
            SocialConnection.platform == platform,
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


def _selected_meta_page(
    pages: list[dict[str, Any]],
    selected_page_id: str | None,
) -> dict[str, Any] | None:
    sid = (selected_page_id or "").strip() or None
    page = None
    if sid:
        page = next((p for p in pages if str(p.get("id")) == str(sid)), None)
    if not page and len(pages) == 1:
        page = pages[0]
    return page if isinstance(page, dict) else None


def _apply_fb_trace(fb_row: SocialConnection, trace: _MetaGraphTrace | None) -> None:
    if not trace:
        return
    fb_row.platform_account_id = trace.page_id
    fb_row.profile_url = trace.facebook_profile_url
    fb_row.page_name = trace.page_display_name
    if trace.ig_username:
        fb_row.account_name = trace.ig_username
    else:
        fb_row.account_name = _strip_or_none(trace.page_username) or trace.page_id


def _apply_ig_trace(ig_row: SocialConnection, trace: _MetaGraphTrace) -> None:
    ig_row.platform_account_id = (trace.ig_account_id or trace.ig_username or "")[:255] or None
    ig_row.profile_url = trace.ig_profile_url
    ig_row.account_name = trace.ig_username
    ig_row.page_name = trace.ig_display_name or trace.page_display_name


def _sync_instagram_row(
    db: Session,
    *,
    idea_id: int,
    user_id: int,
    trace: _MetaGraphTrace | None,
    page: dict[str, Any] | None,
) -> None:
    ig_existing = _row(db, idea_id, PLATFORM_INSTAGRAM_BUSINESS)
    if not page:
        if ig_existing:
            db.delete(ig_existing)
        return

    pid = str(page.get("id") or "").strip()
    tok = str(page.get("access_token") or "").strip()
    if not pid or not tok:
        if ig_existing:
            db.delete(ig_existing)
        return

    if trace is None:
        if ig_existing:
            db.delete(ig_existing)
        return

    if not trace.ig_profile_url:
        if ig_existing:
            db.delete(ig_existing)
        return

    ig_payload = {
        "page_id": pid,
        "page_access_token": tok,
        "instagram_business_account_id": trace.ig_account_id,
    }
    enc = encrypt_json_payload(ig_payload)
    if ig_existing:
        ig_existing.access_token_encrypted = enc
        ig_existing.user_id = user_id
    else:
        ig_existing = SocialConnection(
            user_id=user_id,
            idea_id=idea_id,
            platform=PLATFORM_INSTAGRAM_BUSINESS,
            access_token_encrypted=enc,
        )
        db.add(ig_existing)
    _apply_ig_trace(ig_existing, trace)


def get_connections_for_idea(db: Session, idea_id: int, user_id: int) -> SocialConnectionsOut:
    _assert_idea_owned(db, idea_id, user_id)
    meta_out = None
    li_out = None

    mr = _row(db, idea_id, PLATFORM_FACEBOOK_PAGE)
    if mr:
        data = decrypt_json_payload(mr.access_token_encrypted)
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
        ig_r = _row(db, idea_id, PLATFORM_INSTAGRAM_BUSINESS)
        ig_out = None
        if ig_r:
            ig_out = InstagramBusinessConnectionOut(
                platform_account_id=_strip_or_none(ig_r.platform_account_id),
                profile_url=_strip_or_none(ig_r.profile_url),
                account_name=_strip_or_none(ig_r.account_name),
                page_name=_strip_or_none(ig_r.page_name),
                token_expires_at=ig_r.token_expires_at,
            )
        meta_out = MetaConnectionOut(
            user_access_token=str(data.get("user_access_token") or ""),
            pages=pages,
            selected_page_id=data.get("selected_page_id"),
            account_name=mr.account_name,
            page_name=mr.page_name,
            profile_url=_strip_or_none(mr.profile_url),
            token_expires_at=mr.token_expires_at,
            instagram_business=ig_out,
        )

    lr = _row(db, idea_id, PLATFORM_LINKEDIN)
    if lr:
        data = decrypt_json_payload(lr.access_token_encrypted)
        col_url = _strip_or_none(lr.profile_url)
        li_out = LinkedInConnectionOut(
            access_token=str(data.get("access_token") or ""),
            person_urn=str(data.get("person_urn") or ""),
            name=data.get("name"),
            account_name=lr.account_name,
            page_name=lr.page_name,
            profile_url=col_url or _legacy_linkedin_url_from_payload(data),
            token_expires_at=lr.token_expires_at,
        )
    return SocialConnectionsOut(meta=meta_out, linkedin=li_out)


def upsert_meta(
    db: Session,
    *,
    idea_id: int,
    user_id: int,
    user_access_token: str,
    pages: list[dict[str, Any]],
    selected_page_id: str | None,
    token_expires_at: datetime | None = None,
) -> None:
    _assert_idea_owned(db, idea_id, user_id)
    payload = {
        "user_access_token": user_access_token.strip(),
        "pages": pages,
        "selected_page_id": (selected_page_id or "").strip() or None,
    }
    enc = encrypt_json_payload(payload)
    row = _row(db, idea_id, PLATFORM_FACEBOOK_PAGE)
    if row:
        row.access_token_encrypted = enc
        row.user_id = user_id
    else:
        row = SocialConnection(
            user_id=user_id,
            idea_id=idea_id,
            platform=PLATFORM_FACEBOOK_PAGE,
            access_token_encrypted=enc,
        )
        db.add(row)
    if token_expires_at is not None:
        row.token_expires_at = token_expires_at
    page = _selected_meta_page(pages, payload["selected_page_id"])
    trace = None
    if page:
        pid = str(page.get("id") or "").strip()
        tok = str(page.get("access_token") or "").strip()
        if pid and tok:
            trace = _fetch_meta_graph_trace(pid, tok)
    _apply_fb_trace(row, trace)
    if page:
        _sync_instagram_row(db, idea_id=idea_id, user_id=user_id, trace=trace, page=page)
    else:
        ig_existing = _row(db, idea_id, PLATFORM_INSTAGRAM_BUSINESS)
        if ig_existing:
            db.delete(ig_existing)
    db.commit()


def patch_meta_selected_page(db: Session, *, idea_id: int, user_id: int, selected_page_id: str) -> bool:
    _assert_idea_owned(db, idea_id, user_id)
    row = _row(db, idea_id, PLATFORM_FACEBOOK_PAGE)
    if not row:
        return False
    data = decrypt_json_payload(row.access_token_encrypted)
    page_ids = {str(p.get("id")) for p in (data.get("pages") or [])}
    sid = selected_page_id.strip()
    if sid not in page_ids:
        return False
    data["selected_page_id"] = sid
    row.access_token_encrypted = encrypt_json_payload(data)
    pages = list(data.get("pages") or [])
    page = _selected_meta_page(pages, sid)
    trace = None
    if page:
        pid = str(page.get("id") or "").strip()
        tok = str(page.get("access_token") or "").strip()
        if pid and tok:
            trace = _fetch_meta_graph_trace(pid, tok)
    _apply_fb_trace(row, trace)
    if page:
        _sync_instagram_row(db, idea_id=idea_id, user_id=user_id, trace=trace, page=page)
    else:
        ig_existing = _row(db, idea_id, PLATFORM_INSTAGRAM_BUSINESS)
        if ig_existing:
            db.delete(ig_existing)
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
    token_expires_at: datetime | None = None,
) -> None:
    _assert_idea_owned(db, idea_id, user_id)
    row = _row(db, idea_id, PLATFORM_LINKEDIN)
    prev_profile = _strip_or_none(row.profile_url) if row else None
    if row and not prev_profile:
        try:
            prev_profile = _legacy_linkedin_url_from_payload(
                decrypt_json_payload(row.access_token_encrypted)
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
        row.access_token_encrypted = enc
        row.user_id = user_id
    else:
        row = SocialConnection(
            user_id=user_id,
            idea_id=idea_id,
            platform=PLATFORM_LINKEDIN,
            access_token_encrypted=enc,
        )
        db.add(row)
    if token_expires_at is not None:
        row.token_expires_at = token_expires_at
    t = _fetch_linkedin_public_trace(
        payload["access_token"],
        name,
        payload.get("person_urn"),
    )
    row.account_name = t.account_name
    row.page_name = t.page_name
    row.profile_url = _strip_or_none(t.profile_url) or prev_profile
    urn = (person_urn or "").strip()
    if urn.startswith("urn:li:person:"):
        tail = urn.replace("urn:li:person:", "").strip()
        if tail:
            row.platform_account_id = tail[:255]
    elif t.account_name:
        row.platform_account_id = t.account_name[:255]
    db.commit()


def patch_linkedin_profile_url(
    db: Session,
    *,
    idea_id: int,
    user_id: int,
    profile_url: str | None,
) -> bool:
    _assert_idea_owned(db, idea_id, user_id)
    row = _row(db, idea_id, PLATFORM_LINKEDIN)
    if not row:
        return False
    row.profile_url = profile_url
    try:
        data = decrypt_json_payload(row.access_token_encrypted)
        if isinstance(data, dict):
            cleaned = _payload_without_legacy_linkedin_manual(data)
            if cleaned is not None:
                row.access_token_encrypted = encrypt_json_payload(cleaned)
    except Exception:
        pass
    db.commit()
    return True


def delete_meta(db: Session, *, idea_id: int, user_id: int) -> bool:
    _assert_idea_owned(db, idea_id, user_id)
    q = (
        db.query(SocialConnection)
        .filter(
            SocialConnection.idea_id == idea_id,
            SocialConnection.user_id == user_id,
            SocialConnection.platform.in_(
                (PLATFORM_FACEBOOK_PAGE, PLATFORM_INSTAGRAM_BUSINESS)
            ),
        )
    )
    deleted = q.delete(synchronize_session=False)
    db.commit()
    return deleted > 0


def delete_linkedin(db: Session, *, idea_id: int, user_id: int) -> bool:
    _assert_idea_owned(db, idea_id, user_id)
    row = (
        db.query(SocialConnection)
        .filter(
            SocialConnection.idea_id == idea_id,
            SocialConnection.user_id == user_id,
            SocialConnection.platform == PLATFORM_LINKEDIN,
        )
        .first()
    )
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def get_decrypted_tokens_for_publish(
    db: Session,
    *,
    idea_id: int,
    user_id: int,
    platform_key: str,
) -> dict[str, Any]:
    """platform_key: facebook_page | instagram_business | linkedin"""
    row = (
        db.query(SocialConnection)
        .filter(
            SocialConnection.idea_id == idea_id,
            SocialConnection.user_id == user_id,
            SocialConnection.platform == platform_key,
        )
        .first()
    )
    if not row:
        raise RuntimeError(f"Aucune connexion {platform_key} trouvée.")
    return decrypt_json_payload(row.access_token_encrypted)
