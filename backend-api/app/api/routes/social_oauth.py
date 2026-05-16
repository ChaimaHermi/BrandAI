"""
Routes OAuth Meta (Facebook + Instagram) et LinkedIn.
Toute la logique de connexion aux réseaux sociaux est centralisée ici.
"""

from __future__ import annotations

import logging
import secrets
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.core.oauth_state import (
    save_linkedin_state,
    save_meta_state,
    verify_linkedin_state,
    verify_meta_state,
)
from app.services.linkedin_oauth import (
    LinkedInError,
    build_linkedin_login_url,
    exchange_linkedin_code,
    html_linkedin_oauth_result,
    linkedin_userinfo,
)
from app.services.meta_oauth import (
    MetaGraphError,
    build_meta_login_url,
    exchange_code_for_user_token,
    fetch_pages,
    html_oauth_result,
)

logger = logging.getLogger("brandai.social_oauth")

router = APIRouter(tags=["Social OAuth"])

# ── Config Meta (via pydantic-settings) ───────────────────────
FACEBOOK_APP_ID       = settings.FACEBOOK_APP_ID
FACEBOOK_APP_SECRET   = settings.FACEBOOK_APP_SECRET
META_OAUTH_REDIRECT_URI = settings.META_OAUTH_REDIRECT_URI
META_DEFAULT_SCOPES = [
    "pages_show_list",
    "pages_read_engagement",
    "pages_manage_posts",
    "instagram_basic",
    "instagram_content_publish",
]

# ── Config LinkedIn (via pydantic-settings) ────────────────────
LINKEDIN_CLIENT_ID     = settings.LINKEDIN_CLIENT_ID
LINKEDIN_CLIENT_SECRET = settings.LINKEDIN_PRIMARY_CLIENT_SECRET
LINKEDIN_REDIRECT_URI  = settings.LINKEDIN_REDIRECT_URI
LINKEDIN_SCOPE         = settings.LINKEDIN_SCOPE

FRONTEND_ORIGIN = settings.SOCIAL_OAUTH_FRONTEND_ORIGIN


# ── OAuth Meta ─────────────────────────────────────────────────


@router.get("/social/meta/oauth-url")
async def meta_oauth_url() -> dict[str, str]:
    if not FACEBOOK_APP_ID or not FACEBOOK_APP_SECRET or not META_OAUTH_REDIRECT_URI:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Meta OAuth non configuré (FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, META_OAUTH_REDIRECT_URI).",
        )
    state = secrets.token_urlsafe(16)
    save_meta_state(state)
    url = build_meta_login_url(
        app_id=FACEBOOK_APP_ID,
        redirect_uri=META_OAUTH_REDIRECT_URI,
        scopes=META_DEFAULT_SCOPES,
        state=state,
    )
    return {"url": url, "state": state}


@router.get("/social/meta/callback", response_class=HTMLResponse)
async def meta_oauth_callback(
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    error_description: str | None = Query(None, alias="error_description"),
) -> HTMLResponse:
    if error or error_description:
        msg = error_description or error or "OAuth Meta refusé"
        payload: dict[str, Any] = {
            "type": "brandai-meta-oauth",
            "ok": False,
            "error": msg,
            "oauth_error": error or "",
        }
        return HTMLResponse(html_oauth_result(payload, FRONTEND_ORIGIN))
    if not code or not state:
        payload = {"type": "brandai-meta-oauth", "ok": False, "error": "code ou state manquant"}
        return HTMLResponse(html_oauth_result(payload, FRONTEND_ORIGIN))
    if not verify_meta_state(state):
        payload = {"type": "brandai-meta-oauth", "ok": False, "error": "state invalide ou expiré"}
        return HTMLResponse(html_oauth_result(payload, FRONTEND_ORIGIN))
    try:
        user_token = await exchange_code_for_user_token(
            app_id=FACEBOOK_APP_ID,
            app_secret=FACEBOOK_APP_SECRET,
            redirect_uri=META_OAUTH_REDIRECT_URI,
            code=code,
        )
        pages = await fetch_pages(user_token)
        payload = {
            "type": "brandai-meta-oauth",
            "ok": True,
            "user_access_token": user_token,
            "pages": [
                {"id": p.get("id"), "name": p.get("name"), "access_token": p.get("access_token")}
                for p in pages
                if p.get("id") and p.get("access_token")
            ],
        }
    except MetaGraphError as e:
        logger.warning("meta callback: %s", e)
        payload = {"type": "brandai-meta-oauth", "ok": False, "error": str(e)}
    return HTMLResponse(html_oauth_result(payload, FRONTEND_ORIGIN))


# ── OAuth LinkedIn ─────────────────────────────────────────────


@router.get("/social/linkedin/oauth-url")
async def linkedin_oauth_url() -> dict[str, str]:
    if not LINKEDIN_CLIENT_ID or not LINKEDIN_CLIENT_SECRET or not LINKEDIN_REDIRECT_URI:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="LinkedIn OAuth non configuré (LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, LINKEDIN_REDIRECT_URI).",
        )
    state = secrets.token_urlsafe(16)
    save_linkedin_state(state)
    url = build_linkedin_login_url(
        client_id=LINKEDIN_CLIENT_ID,
        redirect_uri=LINKEDIN_REDIRECT_URI,
        scope=LINKEDIN_SCOPE,
        state=state,
    )
    return {"url": url, "state": state}


@router.get("/social/linkedin/callback", response_class=HTMLResponse)
async def linkedin_oauth_callback(
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    error_description: str | None = Query(None, alias="error_description"),
) -> HTMLResponse:
    if error or error_description:
        msg = error_description or error or "OAuth LinkedIn refusé"
        payload_li: dict[str, Any] = {
            "type": "brandai-linkedin-oauth",
            "ok": False,
            "error": msg,
            "oauth_error": error or "",
        }
        return HTMLResponse(html_linkedin_oauth_result(payload_li, FRONTEND_ORIGIN))
    if not code or not state:
        payload = {"type": "brandai-linkedin-oauth", "ok": False, "error": "code ou state manquant"}
        return HTMLResponse(html_linkedin_oauth_result(payload, FRONTEND_ORIGIN))
    if not verify_linkedin_state(state):
        payload = {"type": "brandai-linkedin-oauth", "ok": False, "error": "state invalide ou expiré"}
        return HTMLResponse(html_linkedin_oauth_result(payload, FRONTEND_ORIGIN))
    try:
        access_token = await exchange_linkedin_code(
            code=code,
            client_id=LINKEDIN_CLIENT_ID,
            client_secret=LINKEDIN_CLIENT_SECRET,
            redirect_uri=LINKEDIN_REDIRECT_URI,
        )
        info = await linkedin_userinfo(access_token)
        sub = info.get("sub") or ""
        person_urn = f"urn:li:person:{sub}" if sub else ""
        payload = {
            "type": "brandai-linkedin-oauth",
            "ok": True,
            "access_token": access_token,
            "person_urn": person_urn,
            "name": info.get("name"),
        }
    except LinkedInError as e:
        logger.warning("linkedin callback: %s", e)
        payload = {"type": "brandai-linkedin-oauth", "ok": False, "error": str(e)}
    return HTMLResponse(html_linkedin_oauth_result(payload, FRONTEND_ORIGIN))
