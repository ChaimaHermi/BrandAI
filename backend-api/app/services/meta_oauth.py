"""Client OAuth Meta (Facebook + Instagram) — fonctions d'authentification uniquement."""

from __future__ import annotations

import base64
import json
import os
from typing import Any
from urllib.parse import urlencode

import httpx

GRAPH_API_VERSION = os.getenv("FACEBOOK_GRAPH_API_VERSION", "v22.0")
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


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
        raise MetaGraphError(
            err.get("message", f"Graph GET {r.status_code}"),
            err.get("code"),
        )
    return data


def build_meta_login_url(
    *,
    app_id: str,
    redirect_uri: str,
    scopes: list[str],
    state: str,
) -> str:
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


def html_oauth_result(payload: dict[str, Any], _frontend_origin: str) -> str:
    b64 = base64.b64encode(
        json.dumps(payload, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")
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
