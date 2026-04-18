"""LinkedIn OAuth + publication UGC (profil)."""

from __future__ import annotations

import base64
import json
import mimetypes
from typing import Any
from urllib.parse import urlencode

import httpx

# Limite prudente (LinkedIn impose des bornes sur la taille des images de partage)
_MAX_IMAGE_BYTES = 8 * 1024 * 1024

AUTHORIZE_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"


class LinkedInError(RuntimeError):
    pass


def build_linkedin_login_url(
    *,
    client_id: str,
    redirect_uri: str,
    scope: str,
    state: str,
) -> str:
    q = urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
        }
    )
    return f"{AUTHORIZE_URL}?{q}"


async def exchange_linkedin_code(
    *,
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        data = r.json() if r.content else {}
    if r.status_code != 200:
        msg = data.get("error_description") or data.get("error") or str(r.status_code)
        raise LinkedInError(f"Token LinkedIn: {msg}")
    token = data.get("access_token")
    if not token:
        raise LinkedInError("Pas d'access_token LinkedIn")
    return str(token)


async def linkedin_userinfo(access_token: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        data = r.json() if r.content else {}
    if r.status_code != 200:
        raise LinkedInError(data.get("message", f"userinfo {r.status_code}"))
    return data


def _parse_register_upload(data: dict[str, Any]) -> tuple[str, str]:
    value = data.get("value") or {}
    asset = str(value.get("asset") or "").strip()
    mech = value.get("uploadMechanism") or {}
    upload_req = mech.get("com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest") or {}
    upload_url = str(upload_req.get("uploadUrl") or "").strip()
    if not asset or not upload_url:
        raise LinkedInError("Réponse registerUpload inattendue (asset ou uploadUrl manquant).")
    return asset, upload_url


async def _download_image_bytes(url: str) -> tuple[bytes, str]:
    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        r = await client.get(url)
        if r.status_code != 200:
            raise LinkedInError(f"Téléchargement image: HTTP {r.status_code}")
        body = r.content
        if len(body) > _MAX_IMAGE_BYTES:
            raise LinkedInError("Image trop volumineuse pour LinkedIn (max ~8 Mo).")
        ct = (r.headers.get("content-type") or "").split(";")[0].strip().lower()
        if not ct or ct == "application/octet-stream":
            path = url.split("?", 1)[0].lower()
            guess, _ = mimetypes.guess_type(path)
            ct = guess or "image/jpeg"
        if not ct.startswith("image/"):
            raise LinkedInError("L’URL ne renvoie pas une image (Content-Type attendu: image/*).")
        return body, ct


async def _register_image_upload(*, access_token: str, owner_urn: str) -> tuple[str, str]:
    body = {
        "registerUploadRequest": {
            "owner": owner_urn,
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent",
                }
            ],
        }
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            "https://api.linkedin.com/v2/assets?action=registerUpload",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            json=body,
        )
        data = r.json() if r.content else {}
    if r.status_code != 200:
        msg = data.get("message") or data.get("error_description") or str(r.status_code)
        raise LinkedInError(f"registerUpload: {msg}")
    return _parse_register_upload(data)


async def _put_image_to_upload_url(upload_url: str, data: bytes, content_type: str) -> None:
    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        r = await client.put(
            upload_url,
            content=data,
            headers={"Content-Type": content_type},
        )
    if r.status_code not in (200, 201):
        raise LinkedInError(f"Envoi binaire image vers LinkedIn: HTTP {r.status_code}")


async def publish_linkedin_ugc(
    *,
    access_token: str,
    person_urn: str,
    message: str,
    image_url: str | None = None,
) -> dict[str, Any]:
    share_content: dict[str, Any] = {
        "shareCommentary": {"text": message},
    }

    img = (image_url or "").strip()
    if img.startswith("https://"):
        # Toujours passer par une URL publique Cloudinary (compte projet) avant LinkedIn :
        # génération → déjà Cloudinary ; sinon ré-import HTTPS → secure_url.
        try:
            from tools.content_generation.cloudinary_upload import ensure_cloudinary_public_url

            public_cdn = await ensure_cloudinary_public_url(img)
        except RuntimeError as e:
            raise LinkedInError(str(e)) from e
        raw, content_type = await _download_image_bytes(public_cdn)
        asset_urn, upload_url = await _register_image_upload(
            access_token=access_token,
            owner_urn=person_urn,
        )
        await _put_image_to_upload_url(upload_url, raw, content_type)
        share_content["shareMediaCategory"] = "IMAGE"
        share_content["media"] = [
            {
                "status": "READY",
                "media": asset_urn,
            }
        ]
    else:
        share_content["shareMediaCategory"] = "NONE"

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            json=payload,
        )
        data = r.json() if r.content else {}
    if r.status_code not in (200, 201):
        raise LinkedInError(data.get("message", f"ugcPosts {r.status_code}"))
    return data


def html_linkedin_oauth_result(payload: dict[str, Any], _frontend_origin: str) -> str:
    """_frontend_origin conservé pour l’appelant ; cible postMessage = * (localhost vs 127.0.0.1, ports Vite)."""
    b64 = base64.b64encode(json.dumps(payload, ensure_ascii=False).encode("utf-8")).decode(
        "ascii"
    )
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"/><title>OAuth LinkedIn</title></head>
<body><p>Connexion LinkedIn reçue. Fermeture…</p>
<script>
(function() {{
  try {{
    var payload = JSON.parse(atob({json.dumps(b64)}));
    if (window.opener) window.opener.postMessage(payload, "*");
  }} catch (e) {{}}
  setTimeout(function() {{ window.close(); }}, 400);
}})();
</script></body></html>"""
