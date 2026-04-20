from __future__ import annotations

import asyncio
import json
import os
import secrets
import sys
import threading
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.social_publish_config import (  # noqa: E402
    LINKEDIN_CLIENT_ID,
    LINKEDIN_CLIENT_SECRET,
    LINKEDIN_REDIRECT_URI,
    LINKEDIN_SCOPE,
)
from tools.social_publishing.linkedin_client import (  # noqa: E402
    build_linkedin_login_url,
    exchange_linkedin_code,
    linkedin_userinfo,
)


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    payload: dict[str, str] = {}
    callback_path: str = "/"
    done_event: threading.Event | None = None

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        _OAuthCallbackHandler.callback_path = parsed.path or "/"
        query = parse_qs(parsed.query or "")
        code = (query.get("code") or [""])[0]
        state = (query.get("state") or [""])[0]
        error = (query.get("error_description") or query.get("error") or [""])[0]

        if not code and not error:
            self.send_response(200)
            self.end_headers()
            return

        _OAuthCallbackHandler.payload = {"code": code, "state": state, "error": error}
        if _OAuthCallbackHandler.done_event:
            _OAuthCallbackHandler.done_event.set()

        body = (
            "<html><body><h3>OAuth reçu.</h3>"
            "<p>Tu peux fermer cet onglet et revenir au terminal.</p></body></html>"
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_args):
        return


def _run_callback_server(redirect_uri: str, timeout_s: int = 240) -> dict[str, str]:
    parsed = urlparse(redirect_uri)
    if parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1"):
        raise RuntimeError(
            "LINKEDIN_TEST_REDIRECT_URI doit être local HTTP (ex: http://localhost:8769/callback)."
        )
    host = parsed.hostname or "localhost"
    port = parsed.port or 80
    expected_path = parsed.path or "/"

    done = threading.Event()
    _OAuthCallbackHandler.payload = {}
    _OAuthCallbackHandler.done_event = done
    server = HTTPServer((host, port), _OAuthCallbackHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        if not done.wait(timeout=timeout_s):
            raise RuntimeError("Timeout OAuth: callback non reçu.")

        payload = _OAuthCallbackHandler.payload
        if payload.get("error"):
            raise RuntimeError(f"OAuth refusé: {payload['error']}")
        if _OAuthCallbackHandler.callback_path != expected_path:
            raise RuntimeError(
                f"Callback inattendu: {_OAuthCallbackHandler.callback_path!r} (attendu: {expected_path!r})."
            )
        if not payload.get("code"):
            raise RuntimeError("Callback reçu mais code manquant.")
        return payload
    finally:
        server.shutdown()
        server.server_close()


async def _fetch_linkedin_collection(
    url: str,
    params: dict[str, str],
    headers: dict[str, str],
    max_items: int,
) -> list[dict]:
    results: list[dict] = []
    start = 0
    count = min(max_items, 100)
    async with httpx.AsyncClient(timeout=60.0) as client:
        while len(results) < max_items:
            paged_params = {**params, "start": str(start), "count": str(count)}
            r = await client.get(url, headers=headers, params=paged_params)
            if r.status_code != 200:
                body = r.text[:1000] if r.text else ""
                print(
                    f"[LinkedIn] collection non-200: HTTP {r.status_code} on {url}\n"
                    f"params={paged_params}\nbody={body}",
                    flush=True,
                )
                break
            data = r.json() if r.content else {}
            elements = data.get("elements") or []
            if not isinstance(elements, list) or not elements:
                break
            for e in elements:
                if isinstance(e, dict):
                    results.append(e)
                if len(results) >= max_items:
                    break
            if len(elements) < count:
                break
            start += count
    return results[:max_items]


async def _get_social_actions(access_token: str, activity_urn: str) -> dict | None:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    url = f"https://api.linkedin.com/v2/socialActions/{activity_urn}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(url, headers=headers)
        if r.status_code != 200:
            return None
        return r.json() if r.content else {}


def _extract_sort_key(item: dict) -> int:
    # LinkedIn returns different timestamp fields depending on endpoint.
    candidates = [
        (item.get("lastModified") or {}).get("time"),
        (item.get("created") or {}).get("time"),
        (item.get("createdTime")),
    ]
    for value in candidates:
        try:
            if value is not None:
                return int(value)
        except Exception:
            continue
    return 0


def _read_local_posts_log() -> list[dict]:
    """
    Fallback local cache compatible with LinkedInPublisher example:
    scripts/linkedin_posts_log.json
    """
    log_path = ROOT / "scripts" / "linkedin_posts_log.json"
    if not log_path.exists():
        return []
    try:
        data = json.loads(log_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return [x for x in data if isinstance(x, dict)]


async def _main() -> None:
    redirect_uri = (
        os.getenv("LINKEDIN_TEST_REDIRECT_URI")
        or LINKEDIN_REDIRECT_URI
        or "http://localhost:8769/callback"
    ).strip()
    posts_limit = int(os.getenv("LINKEDIN_EXTRACT_LIMIT") or "10")
    oauth_timeout_s = int(os.getenv("LINKEDIN_OAUTH_TIMEOUT_S") or "240")

    if not LINKEDIN_CLIENT_ID or not LINKEDIN_CLIENT_SECRET:
        raise RuntimeError("LINKEDIN_CLIENT_ID / LINKEDIN_CLIENT_SECRET manquants dans .env")

    state = secrets.token_urlsafe(16)
    oauth_url = build_linkedin_login_url(
        client_id=LINKEDIN_CLIENT_ID,
        redirect_uri=redirect_uri,
        scope=LINKEDIN_SCOPE,
        state=state,
    )

    print("\nCONNECT LinkedIn Profil (ouverture navigateur):\n", flush=True)
    print(oauth_url, flush=True)
    print(f"Redirect URI utilisee par le script: {redirect_uri}", flush=True)
    print(f"\nAttente du callback OAuth... (timeout {oauth_timeout_s}s)\n", flush=True)
    webbrowser.open(oauth_url)

    payload = await asyncio.to_thread(_run_callback_server, redirect_uri, oauth_timeout_s)
    code = payload.get("code") or ""
    returned_state = payload.get("state") or ""
    if returned_state != state:
        raise RuntimeError("State OAuth invalide.")

    access_token = await exchange_linkedin_code(
        code=code,
        client_id=LINKEDIN_CLIENT_ID,
        client_secret=LINKEDIN_CLIENT_SECRET,
        redirect_uri=redirect_uri,
    )
    profile = await linkedin_userinfo(access_token)
    sub = str(profile.get("sub") or "").strip()
    if not sub:
        raise RuntimeError("Impossible de récupérer 'sub' depuis LinkedIn userinfo.")
    person_urn = f"urn:li:person:{sub}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    ugc_url = "https://api.linkedin.com/v2/ugcPosts"
    shares_url = "https://api.linkedin.com/v2/shares"

    ugc_posts = await _fetch_linkedin_collection(
        ugc_url,
        {"q": "authors", "authors": f"List({person_urn})"},
        headers,
        posts_limit,
    )
    shares_posts = await _fetch_linkedin_collection(
        shares_url,
        {"q": "owners", "owners": f"List({person_urn})"},
        headers,
        posts_limit,
    )

    merged: dict[str, dict] = {}
    for p in ugc_posts:
        pid = str(p.get("id") or "").strip()
        if pid:
            merged[pid] = p
    for p in shares_posts:
        pid = str(p.get("id") or "").strip()
        if pid and pid not in merged:
            merged[pid] = p

    posts = sorted(merged.values(), key=_extract_sort_key, reverse=True)[:posts_limit]
    print(
        f"Sources posts LinkedIn: ugcPosts={len(ugc_posts)}, shares={len(shares_posts)} => selected={len(posts)}",
        flush=True,
    )

    local_posts = _read_local_posts_log()
    local_posts_used = False
    if not posts and local_posts:
        # Convert local published-post cache to the script's output structure.
        posts = []
        for p in local_posts[:posts_limit]:
            pid = str(p.get("id") or "").strip()
            msg = p.get("message")
            published_at = p.get("published_at")
            posts.append(
                {
                    "id": pid or None,
                    "source": "local_cache",
                    "local_author": p.get("author"),
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {"text": msg or ""},
                            "shareMediaCategory": "NONE",
                        }
                    },
                    "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
                    "lastModified": {"time": None},
                    "created": {"time": None},
                    "published_at": published_at,
                }
            )
        local_posts_used = True
        print(
            f"API posts unavailable; fallback local cache used: {len(posts)} post(s).",
            flush=True,
        )

    posts_detailed: list[dict] = []
    for post in posts:
        post_id = str(post.get("id") or "").strip()
        social_actions = None
        if post_id and not local_posts_used:
            social_actions = await _get_social_actions(access_token, post_id)
        posts_detailed.append(
            {
                "post": post,
                "social_actions": social_actions,
            }
        )

    out = {
        "platform": "linkedin",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "profile": {
            "sub": sub,
            "person_urn": person_urn,
            "name": profile.get("name"),
            "email": profile.get("email"),
            "profile_raw": profile,
        },
        "posts_count": len(posts),
        "posts": posts,
        "posts_detailed": posts_detailed,
        "extract_config": {
            "posts_limit": posts_limit,
            "null_when_unavailable": True,
            "sources": {
                "ugc_posts_count": len(ugc_posts),
                "shares_count": len(shares_posts),
                "local_cache_count": len(local_posts),
                "local_cache_used": local_posts_used,
            },
        },
    }

    out_dir = ROOT / "scripts" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "linkedin_extract_result.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nExtraction terminee.", flush=True)
    print(f"JSON enregistre: {out_path}\n", flush=True)


if __name__ == "__main__":
    asyncio.run(_main())

