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
    FACEBOOK_APP_ID,
    FACEBOOK_APP_SECRET,
    META_DEFAULT_SCOPES,
)
from tools.social_publishing.meta_client import (  # noqa: E402
    _graph_get,
    build_meta_login_url,
    exchange_code_for_user_token,
    fetch_pages,
    get_instagram_business_account_id,
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
            "META_TEST_REDIRECT_URI doit être local HTTP (ex: http://localhost:8768/callback)."
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


async def _fetch_graph_collection(
    *,
    path: str,
    params: dict,
    max_items: int,
) -> list[dict]:
    results: list[dict] = []
    try:
        data = await _graph_get(path, params)
    except Exception as e:
        print(f"[Graph] collection error on {path}: {e}", flush=True)
        return results

    while True:
        items = data.get("data") or []
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    results.append(item)
                if len(results) >= max_items:
                    return results[:max_items]

        next_url = ((data.get("paging") or {}).get("next") or "").strip()
        if not next_url or len(results) >= max_items:
            return results[:max_items]

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.get(next_url)
                data = r.json() if r.content else {}
            if r.status_code != 200:
                print(f"[Graph] paging non-200 on {path}: HTTP {r.status_code}", flush=True)
                return results[:max_items]
        except Exception as e:
            print(f"[Graph] paging error on {path}: {e}", flush=True)
            return results[:max_items]


async def _safe_graph_get(path: str, params: dict) -> dict | None:
    try:
        return await _graph_get(path, params)
    except Exception:
        return None


async def _main() -> None:
    redirect_uri = (
        os.getenv("META_TEST_REDIRECT_URI") or "http://localhost:8768/callback"
    ).strip()
    media_limit = int(os.getenv("INSTAGRAM_EXTRACT_LIMIT") or "10")
    comments_limit = int(os.getenv("INSTAGRAM_COMMENTS_LIMIT") or "100")
    oauth_timeout_s = int(os.getenv("META_TEST_OAUTH_TIMEOUT_S") or "240")

    if not FACEBOOK_APP_ID or not FACEBOOK_APP_SECRET:
        raise RuntimeError("FACEBOOK_APP_ID / FACEBOOK_APP_SECRET manquants dans .env")

    scopes = list(
        dict.fromkeys(
            [
                *META_DEFAULT_SCOPES,
                "pages_manage_metadata",
                "pages_read_user_content",
                "instagram_manage_comments",
                "instagram_manage_insights",
            ]
        )
    )

    def choose_page(pages: list[dict]) -> dict:
        print("\nPages disponibles:", flush=True)
        for idx, p in enumerate(pages, start=1):
            print(f"  {idx}. {p.get('name')} (id={p.get('id')})", flush=True)
        while True:
            raw = input("\nChoisis le numero de page a utiliser pour Instagram: ").strip()
            try:
                n = int(raw)
                if 1 <= n <= len(pages):
                    return pages[n - 1]
            except Exception:
                pass
            print("Choix invalide. Reessaye.", flush=True)

    state = secrets.token_urlsafe(16)
    oauth_url = build_meta_login_url(
        app_id=FACEBOOK_APP_ID,
        redirect_uri=redirect_uri,
        scopes=scopes,
        state=state,
    )

    print("\nCONNECT Instagram/Meta (ouverture navigateur):\n", flush=True)
    print(oauth_url, flush=True)
    print(f"\nAttente du callback OAuth... (timeout {oauth_timeout_s}s)\n", flush=True)
    webbrowser.open(oauth_url)

    payload = await asyncio.to_thread(_run_callback_server, redirect_uri, oauth_timeout_s)
    code = payload.get("code") or ""
    returned_state = payload.get("state") or ""
    if returned_state != state:
        raise RuntimeError("State OAuth invalide.")

    user_token = await exchange_code_for_user_token(
        app_id=FACEBOOK_APP_ID,
        app_secret=FACEBOOK_APP_SECRET,
        redirect_uri=redirect_uri,
        code=code,
    )
    pages = await fetch_pages(user_token)
    pages = [p for p in pages if p.get("id") and p.get("access_token")]
    if not pages:
        raise RuntimeError("Aucune page trouvée (token sans accès page).")

    print(f"\nOAuth a retourne {len(pages)} page(s).", flush=True)
    page = await asyncio.to_thread(choose_page, pages)
    page_id = str(page["id"])
    page_token = str(page["access_token"])

    ig_user_id = await get_instagram_business_account_id(page_id, page_token)
    print(f"Instagram business account id: {ig_user_id}", flush=True)

    media = await _fetch_graph_collection(
        path=f"{ig_user_id}/media",
        params={
            "fields": (
                "id,caption,media_type,media_url,permalink,timestamp,thumbnail_url,"
                "like_count,comments_count"
            ),
            "limit": min(media_limit, 100),
            "access_token": page_token,
        },
        max_items=media_limit,
    )

    detailed: list[dict] = []
    for item in media:
        media_id = str(item.get("id") or "").strip()
        if not media_id:
            continue

        insights = await _safe_graph_get(
            media_id,
            {
                "fields": "insights.metric(impressions,reach,saved,shares,engagement)",
                "access_token": page_token,
            },
        )
        insights_data = None
        if insights and isinstance((insights.get("insights") or {}).get("data"), list):
            insights_data = (insights.get("insights") or {}).get("data")

        comments = await _fetch_graph_collection(
            path=f"{media_id}/comments",
            params={
                "fields": "id,text,timestamp,username,like_count,replies_count",
                "limit": min(comments_limit, 100),
                "access_token": page_token,
            },
            max_items=comments_limit,
        )
        if not comments:
            comments = None

        detailed.append(
            {
                "media": item,
                "insights": insights_data,
                "comments": comments,
                "comments_count_fetched": len(comments) if comments else None,
            }
        )

    out = {
        "platform": "instagram",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "page": {"id": page_id, "name": page.get("name")},
        "instagram_user_id": ig_user_id,
        "media_count": len(media),
        "media": media,
        "media_detailed": detailed,
        "extract_config": {
            "media_limit": media_limit,
            "comments_limit_per_media": comments_limit,
            "null_when_unavailable": True,
        },
    }

    out_dir = ROOT / "scripts" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "instagram_extract_result.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nExtraction terminee.", flush=True)
    print(f"JSON enregistre: {out_path}\n", flush=True)


if __name__ == "__main__":
    asyncio.run(_main())

