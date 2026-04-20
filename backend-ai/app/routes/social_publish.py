"""
OAuth Meta / LinkedIn + publication (Facebook Page, Instagram Business, LinkedIn profil).
Configurez les redirect URIs dans les consoles développeur pour pointer vers ces callbacks.
"""

from __future__ import annotations

import logging
import secrets
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from config.social_publish_config import (
    FACEBOOK_APP_ID,
    FACEBOOK_APP_SECRET,
    FACEBOOK_PAGE_ACCESS_TOKEN,
    FACEBOOK_PAGE_ID,
    FRONTEND_ORIGIN,
    LINKEDIN_CLIENT_ID,
    LINKEDIN_CLIENT_SECRET,
    LINKEDIN_REDIRECT_URI,
    LINKEDIN_SCOPE,
    META_DEFAULT_SCOPES,
    META_OAUTH_REDIRECT_URI,
)
from tools.social_publishing.linkedin_client import (
    LinkedInError,
    build_linkedin_login_url,
    exchange_linkedin_code,
    html_linkedin_oauth_result,
    linkedin_userinfo,
    publish_linkedin_ugc,
)
from tools.social_publishing.meta_client import (
    MetaGraphError,
    build_meta_login_url,
    exchange_code_for_user_token,
    fetch_pages,
    get_instagram_business_account_id,
    html_oauth_result,
    publish_instagram_photo,
    publish_page_feed,
)
from tools.social_publishing.oauth_state import (
    save_linkedin_state,
    save_meta_state,
    verify_linkedin_state,
    verify_meta_state,
)

logger = logging.getLogger("brandai.social_publish")

router = APIRouter(tags=["Social Publish"])


async def _ensure_cloudinary_https_for_publish(image_url: str) -> str:
    """Toute image publiée vers les réseaux passe par une URL `secure` du compte Cloudinary du projet."""
    from tools.content_generation.cloudinary_upload import ensure_cloudinary_public_url

    try:
        return await ensure_cloudinary_public_url(image_url)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ── OAuth Meta ─────────────────────────────────────────────────────────────


@router.get("/social/meta/oauth-url")
async def meta_oauth_url() -> dict[str, str]:
    if not FACEBOOK_APP_ID or not FACEBOOK_APP_SECRET or not META_OAUTH_REDIRECT_URI:
        raise HTTPException(
            status_code=503,
            detail="Meta OAuth non configuré (FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, META_OAUTH_REDIRECT_URI ou FACEBOOK_REDIRECT_URI).",
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
        # error ex. access_denied quand l'utilisateur choisit « plus tard » ou ferme la fenêtre
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
        # Ne pas renvoyer le user_token au front si possible — ici nécessaire pour rafraîchir me/accounts
        payload: dict[str, Any] = {
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


# ── OAuth LinkedIn ─────────────────────────────────────────────────────────


@router.get("/social/linkedin/oauth-url")
async def linkedin_oauth_url() -> dict[str, str]:
    if not LINKEDIN_CLIENT_ID or not LINKEDIN_CLIENT_SECRET or not LINKEDIN_REDIRECT_URI:
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


# ── Publication ─────────────────────────────────────────────────────────────


class FacebookPublishBody(BaseModel):
    message: str = Field(..., min_length=1)
    page_id: str | None = None
    page_access_token: str | None = None
    link: str | None = Field(None, description="URL publique pour aperçu lien (ex. image Cloudinary)")


@router.post("/social/publish/facebook")
async def publish_facebook(body: FacebookPublishBody) -> dict[str, Any]:
    page_id = (body.page_id or FACEBOOK_PAGE_ID or "").strip()
    token = (body.page_access_token or FACEBOOK_PAGE_ACCESS_TOKEN or "").strip()
    if not page_id or not token:
        raise HTTPException(
            status_code=400,
            detail="page_id et page_access_token requis (ou FACEBOOK_PAGE_ID + FACEBOOK_PAGE_ACCESS_TOKEN dans .env).",
        )
    link = (body.link or "").strip() or None
    if link and link.startswith("https://"):
        link = await _ensure_cloudinary_https_for_publish(link)
    try:
        out = await publish_page_feed(
            page_id=page_id,
            page_access_token=token,
            message=body.message.strip(),
            link=link,
        )
        return {"ok": True, "platform": "facebook", "result": out}
    except MetaGraphError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


class InstagramPublishBody(BaseModel):
    caption: str = Field(..., min_length=1)
    image_url: str = Field(..., min_length=12, description="URL HTTPS publique (ex. Cloudinary)")
    page_id: str = Field(..., min_length=1)
    page_access_token: str = Field(..., min_length=1)


@router.post("/social/publish/instagram")
async def publish_instagram(body: InstagramPublishBody) -> dict[str, Any]:
    url = body.image_url.strip()
    if not url.startswith("https://"):
        raise HTTPException(
            status_code=400,
            detail="image_url doit être en HTTPS (exigence Instagram).",
        )
    url = await _ensure_cloudinary_https_for_publish(url)
    try:
        ig_id = await get_instagram_business_account_id(
            body.page_id.strip(), body.page_access_token.strip()
        )
        out = await publish_instagram_photo(
            ig_user_id=ig_id,
            page_access_token=body.page_access_token.strip(),
            image_url=url,
            caption=body.caption.strip(),
        )
        return {"ok": True, "platform": "instagram", "instagram_user_id": ig_id, "result": out}
    except MetaGraphError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


class LinkedInPublishBody(BaseModel):
    message: str = Field(..., min_length=1)
    access_token: str | None = None
    person_urn: str | None = None
    image_url: str | None = Field(
        None,
        description="URL HTTPS publique de l’image (ex. Cloudinary) — enregistrée puis jointe au post.",
    )


@router.post("/social/publish/linkedin")
async def publish_linkedin_route(body: LinkedInPublishBody) -> dict[str, Any]:
    import os

    token = (body.access_token or os.getenv("LINKEDIN_ACCESS_TOKEN") or "").strip()
    if not token:
        raise HTTPException(
            status_code=400,
            detail="access_token requis (corps ou LINKEDIN_ACCESS_TOKEN dans .env).",
        )
    person_urn = (body.person_urn or "").strip()
    if not person_urn:
        try:
            info = await linkedin_userinfo(token)
            sub = info.get("sub") or ""
            if not sub:
                raise LinkedInError("sub manquant dans userinfo")
            person_urn = f"urn:li:person:{sub}"
        except LinkedInError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    try:
        img = (body.image_url or "").strip()
        out = await publish_linkedin_ugc(
            access_token=token,
            person_urn=person_urn,
            message=body.message.strip(),
            image_url=img if img.startswith("https://") else None,
        )
        return {"ok": True, "platform": "linkedin", "result": out}
    except LinkedInError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
