"""Client OAuth LinkedIn — fonctions d'authentification uniquement."""

from __future__ import annotations

import base64
import json
from typing import Any
from urllib.parse import urlencode

import httpx

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
            "prompt": "login",
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


def html_linkedin_oauth_result(payload: dict[str, Any], _frontend_origin: str) -> str:
    b64 = base64.b64encode(
        json.dumps(payload, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")
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
