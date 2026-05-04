"""Server-side social publisher — calls backend-ai /social/publish/* endpoints."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("brandai.platform_publisher")

AI_BASE = os.getenv("AI_BASE_URL", "http://localhost:8001/api/ai")
TIMEOUT = httpx.Timeout(120.0, connect=10.0)


async def publish_to_platform(
    *,
    platform: str,
    caption: str,
    image_url: str | None,
    social_tokens: dict[str, Any],
) -> dict[str, Any]:
    """Publish a post to one platform via backend-ai social endpoints.

    `social_tokens` is the decrypted payload from `social_connections.access_token_encrypted` :
      facebook_page → {pages: [...], selected_page_id, user_access_token}
      instagram_business → {page_id, page_access_token, instagram_business_account_id?}
      linkedin → {access_token, person_urn}
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        if platform == "facebook":
            page = _resolve_meta_page(social_tokens)
            body: dict[str, Any] = {
                "message": caption,
                "page_id": str(page["id"]),
                "page_access_token": str(page.get("access_token", "")),
            }
            if image_url and image_url.startswith("https"):
                body["link"] = image_url
            r = await client.post(f"{AI_BASE}/social/publish/facebook", json=body)

        elif platform == "instagram":
            if not image_url or not image_url.startswith("https"):
                raise RuntimeError("Instagram requiert une image HTTPS publique.")
            page = _resolve_meta_page(social_tokens)
            body = {
                "caption": caption,
                "image_url": image_url,
                "page_id": str(page["id"]),
                "page_access_token": str(page.get("access_token", "")),
            }
            r = await client.post(f"{AI_BASE}/social/publish/instagram", json=body)

        elif platform == "linkedin":
            access_token = social_tokens.get("access_token")
            if not access_token:
                raise RuntimeError("Token LinkedIn manquant. Reconnectez votre compte.")
            body = {"message": caption, "access_token": access_token}
            if social_tokens.get("person_urn"):
                body["person_urn"] = social_tokens["person_urn"]
            if image_url and image_url.startswith("https"):
                body["image_url"] = image_url
            r = await client.post(f"{AI_BASE}/social/publish/linkedin", json=body)

        else:
            raise RuntimeError(f"Plateforme non supportée: {platform}")

        data = r.json() if r.content else {}
        if r.status_code not in (200, 201):
            detail = data.get("detail") if isinstance(data, dict) else str(data)
            raise RuntimeError(f"Erreur publication {platform}: {detail}")
        return data


def _resolve_meta_page(social_tokens: dict[str, Any]) -> dict[str, Any]:
    pages = social_tokens.get("pages")
    if isinstance(pages, list) and pages:
        page_id = social_tokens.get("selected_page_id")
        page = next((p for p in pages if str(p.get("id")) == str(page_id)), None)
        if not page and len(pages) == 1:
            page = pages[0]
        if page and page.get("id") and page.get("access_token"):
            return page
    pid = social_tokens.get("page_id")
    tok = social_tokens.get("page_access_token")
    if pid and tok:
        return {"id": str(pid), "access_token": str(tok)}
    raise RuntimeError("Aucune page Facebook sélectionnée ou token invalide.")
