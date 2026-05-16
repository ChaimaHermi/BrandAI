"""
Publication sociale (Facebook Page, Instagram Business, LinkedIn profil).
Les routes OAuth (connexion) ont été migrées vers backend-api/app/api/routes/social_oauth.py.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config.social_publish_config import (
    FACEBOOK_PAGE_ACCESS_TOKEN,
    FACEBOOK_PAGE_ID,
)
from tools.social_publishing.linkedin_client import (
    LinkedInError,
    publish_linkedin_ugc,
)
from tools.social_publishing.meta_client import (
    MetaGraphError,
    get_instagram_business_account_id,
    publish_instagram_photo,
    publish_page_feed,
)

logger = logging.getLogger("brandai.social_publish")

router = APIRouter(tags=["Social Publish"])


async def _ensure_cloudinary_https_for_publish(image_url: str) -> str:
    from tools.content_generation.cloudinary_upload import ensure_cloudinary_public_url

    try:
        return await ensure_cloudinary_public_url(image_url)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


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
