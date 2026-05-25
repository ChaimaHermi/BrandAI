"""Client Graph API Meta (Facebook Page + Instagram Business) — httpx async."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
from typing import Any

import httpx

from config.social_publish_config import GRAPH_API_VERSION

logger = logging.getLogger("brandai.meta_client")

BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

# Subcodes Meta retriables lors du polling conteneur IG (média pas encore prêt).
_IG_STATUS_RETRY_SUBCODES = frozenset({2207027, 2207050})


def _ig_status_auth_error_message(err: dict[str, Any]) -> str:
    return (
        "Erreur d'autorisation Meta pour la vérification Instagram (code 100/33). "
        "Déconnectez puis reconnectez votre compte Meta dans l'application. "
        f"Détail Meta : {err.get('message', 'Authorization Error')}"
    )


class MetaGraphError(RuntimeError):
    def __init__(self, message: str, code: str | int | None = None):
        self.code = code
        super().__init__(message)


async def _graph_get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(f"{BASE}/{path.lstrip('/')}", params=params)
        data = r.json() if r.content else {}
    if r.status_code != 200:
        err = data.get("error") or {}
        msg = err.get("message", f"Graph GET {r.status_code}")
        logger.warning(
            "[meta_client] Graph GET %s | code=%s subcode=%s | %s",
            r.status_code,
            err.get("code"),
            err.get("error_subcode"),
            msg,
        )
        raise MetaGraphError(msg, err.get("code"))
    return data


async def _graph_post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(f"{BASE}/{path.lstrip('/')}", data=payload)
        data = r.json() if r.content else {}
    if r.status_code != 200:
        err = data.get("error") or {}
        msg = err.get("message", f"Graph POST {r.status_code}")
        logger.warning(
            "[meta_client] Graph POST %s | code=%s subcode=%s | %s",
            r.status_code,
            err.get("code"),
            err.get("error_subcode"),
            msg,
        )
        raise MetaGraphError(msg, err.get("code"))
    return data


def build_meta_login_url(
    *,
    app_id: str,
    redirect_uri: str,
    scopes: list[str],
    state: str,
) -> str:
    from urllib.parse import urlencode

    q = urlencode(
        {
            "client_id": app_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": ",".join(scopes),
            "state": state,
        }
    )
    return f"https://www.facebook.com/{GRAPH_API_VERSION}/dialog/oauth?{q}"


async def exchange_code_for_user_token(
    *,
    app_id: str,
    app_secret: str,
    redirect_uri: str,
    code: str,
) -> str:
    data = await _graph_get(
        "oauth/access_token",
        {
            "client_id": app_id,
            "client_secret": app_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        },
    )
    token = data.get("access_token")
    if not token:
        raise MetaGraphError("Pas de access_token Meta")
    return str(token)


async def fetch_pages(user_access_token: str) -> list[dict[str, Any]]:
    data = await _graph_get(
        "me/accounts",
        {
            "fields": "id,name,access_token,tasks",
            "access_token": user_access_token,
        },
    )
    return list(data.get("data") or [])


async def publish_page_feed(
    *,
    page_id: str,
    page_access_token: str,
    message: str,
    link: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, str] = {
        "message": message,
        "access_token": page_access_token,
    }
    if link:
        payload["link"] = link
    return await _graph_post(f"{page_id}/feed", payload)


async def get_instagram_business_account_id(
    page_id: str, page_access_token: str
) -> str:
    data = await _graph_get(
        page_id,
        {
            "fields": "instagram_business_account",
            "access_token": page_access_token,
        },
    )
    ig = data.get("instagram_business_account") or {}
    ig_id = ig.get("id")
    if not ig_id:
        raise MetaGraphError(
            "Aucun compte Instagram professionnel lié à cette Page Facebook."
        )
    return str(ig_id)


async def _fetch_ig_container_status(
    creation_id: str, status_access_token: str
) -> dict[str, Any]:
    """Interroge le conteneur IG. Lève MetaGraphError si erreur non retriable."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(
            f"{BASE}/{creation_id.lstrip('/')}",
            params={"fields": "status_code", "access_token": status_access_token},
        )
        data = r.json() if r.content else {}
    if r.status_code == 200:
        return data
    err = data.get("error") or {}
    msg = err.get("message", f"Graph GET {r.status_code}")
    subcode = err.get("error_subcode")
    code = err.get("code")
    logger.warning(
        "[meta_client] IG container %s status GET %s | code=%s subcode=%s | %s",
        creation_id,
        r.status_code,
        code,
        subcode,
        msg,
    )
    if subcode == 33:
        raise MetaGraphError(_ig_status_auth_error_message(err), code)
    if subcode in _IG_STATUS_RETRY_SUBCODES:
        return {"status_code": "IN_PROGRESS"}
    raise MetaGraphError(msg, code)


async def _wait_ig_container_ready(
    creation_id: str,
    status_access_token: str,
    *,
    timeout_s: float = 120.0,
) -> None:
    """Attend status_code FINISHED. Utiliser le user access token Meta (pas le page token)."""
    await asyncio.sleep(5.0)
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        data = await _fetch_ig_container_status(creation_id, status_access_token)
        status = str(data.get("status_code") or "").upper()
        if status in ("FINISHED", "PUBLISHED"):
            logger.info(
                "[meta_client] IG container %s ready | status_code=%s",
                creation_id,
                status,
            )
            return
        if status in ("ERROR", "EXPIRED"):
            raise MetaGraphError(
                f"Conteneur Instagram en erreur: {data.get('status')!r}", status
            )
        await asyncio.sleep(5.0)
    raise MetaGraphError("Timeout attente traitement média Instagram")


async def publish_instagram_photo(
    *,
    ig_user_id: str,
    page_access_token: str,
    image_url: str,
    caption: str,
    user_access_token: str | None = None,
) -> dict[str, Any]:
    create = await _graph_post(
        f"{ig_user_id}/media",
        {
            "image_url": image_url,
            "caption": caption,
            "access_token": page_access_token,
        },
    )
    creation_id = create.get("id")
    if not creation_id:
        raise MetaGraphError("Création conteneur Instagram sans id")
    status_token = (user_access_token or "").strip()
    if not status_token:
        raise MetaGraphError(
            "user_access_token Meta requis pour publier sur Instagram "
            "(reconnectez votre compte Meta dans l'application)."
        )
    await _wait_ig_container_ready(str(creation_id), status_token)
    published = await _graph_post(
        f"{ig_user_id}/media_publish",
        {
            "creation_id": str(creation_id),
            "access_token": page_access_token,
        },
    )
    return {"creation_id": str(creation_id), **published}


def html_oauth_result(payload: dict[str, Any], _frontend_origin: str) -> str:
    """Réponse HTML : postMessage vers l’onglet parent puis fermeture. Cible * pour tout hôte local Vite."""
    b64 = base64.b64encode(json.dumps(payload, ensure_ascii=False).encode("utf-8")).decode(
        "ascii"
    )
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"/><title>OAuth Meta</title></head>
<body><p>Connexion Meta reçue. Fermeture…</p>
<script>
(function() {{
  try {{
    var payload = JSON.parse(atob({json.dumps(b64)}));
    if (window.opener) window.opener.postMessage(payload, "*");
  }} catch (e) {{}}
  setTimeout(function() {{ window.close(); }}, 400);
}})();
</script></body></html>"""
