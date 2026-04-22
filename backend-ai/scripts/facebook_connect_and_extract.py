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
from tools.social_optimizer.collectors.meta_collector import MetaCollector  # noqa: E402
from tools.social_publishing.meta_client import (  # noqa: E402
    BASE,
    _graph_get,
    build_meta_login_url,
    exchange_code_for_user_token,
    fetch_pages,
    MetaGraphError,
)

FACEBOOK_PAGE_INSIGHT_METRICS = [
    "page_impressions_unique",
    "page_post_engagements",
    "page_views_total",
    "page_fans_online",
    "page_actions_post_reactions_total",
    "page_actions_post_comments_total",
    "page_actions_post_shares_total",
    "page_impressions",
]

FACEBOOK_POST_INSIGHT_METRICS = [
    "post_impressions_unique",
    "post_clicks",
    "post_reactions_like_total",
    "post_reactions_love_total",
    "post_reactions_wow_total",
    "post_reactions_haha_total",
    "post_reactions_sorry_total",
    "post_reactions_anger_total",
    "post_video_views",
    "post_video_complete_views_organic",
    "post_impressions_paid",
    "post_impressions_fan",
    "post_impressions_organic",
    "post_impressions",
    "post_engaged_users",
    "post_comments",
    "post_shares",
]


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
            body = (
                "<html><body><h3>Callback reçu, en attente des paramètres OAuth...</h3>"
                "</body></html>"
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
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


async def _safe_graph_get(path: str, params: dict) -> dict | None:
    try:
        return await _graph_get(path, params)
    except Exception:
        return None


async def _safe_graph_get_with_error(path: str, params: dict) -> tuple[dict | None, dict | None]:
    try:
        return await _graph_get(path, params), None
    except MetaGraphError as e:
        return None, {"message": str(e), "code": e.code}
    except Exception as e:
        return None, {"message": str(e), "code": None}


async def _fetch_insights_metrics_debug(
    *,
    object_id: str,
    metrics: list[str],
    access_token: str,
    period: str | None = None,
) -> tuple[list[dict] | None, dict | None]:
    """
    Fetch insights metrics one by one to avoid complete failure when one metric is invalid.
    Returns combined data + debug info (accepted/rejected metrics).
    """
    combined: list[dict] = []
    accepted: list[str] = []
    rejected: list[dict] = []

    total_metrics = len(metrics)
    for metric_idx, metric in enumerate(metrics, start=1):
        print(
            f"[insights][{object_id}] metric {metric_idx}/{total_metrics}: {metric}",
            flush=True,
        )
        params: dict[str, str] = {"metric": metric, "access_token": access_token}
        if period:
            params["period"] = period
        data, err = await _safe_graph_get_with_error(f"{object_id}/insights", params)
        if data and isinstance(data.get("data"), list):
            rows = [x for x in (data.get("data") or []) if isinstance(x, dict)]
            if rows:
                combined.extend(rows)
                accepted.append(metric)
                continue
        rejected.append({"metric": metric, "error": err})

    debug = {
        "requested_metrics": metrics,
        "accepted_metrics": accepted,
        "rejected_metrics": rejected,
    }
    return (combined or None), debug


async def _fetch_graph_collection(
    *,
    path: str,
    params: dict,
    max_items: int,
) -> list[dict]:
    """
    Read paginated Graph collections up to max_items.
    Returns [] if request fails.
    """
    results: list[dict] = []
    try:
        data = await _graph_get(path, params)
    except Exception as e:
        print(f"[Graph] collection error on {path}: {e}", flush=True)
        return results

    while True:
        page_items = data.get("data") or []
        if isinstance(page_items, list):
            for item in page_items:
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


def _extract_insight_value(insights: list[dict] | None, metric_name: str) -> int | None:
    if not insights:
        return None
    for item in insights:
        if not isinstance(item, dict):
            continue
        if str(item.get("name") or "") != metric_name:
            continue
        values = item.get("values")
        if isinstance(values, list) and values:
            raw = values[0] if isinstance(values[0], dict) else {}
            value = raw.get("value") if isinstance(raw, dict) else None
            if isinstance(value, (int, float)):
                return int(value)
    return None


def _facebook_post_type_api(post: dict[str, Any]) -> str:
    status_type = str(post.get("status_type") or "").strip().lower()
    attachments = post.get("attachments")
    if isinstance(attachments, dict):
        data = attachments.get("data")
        if isinstance(data, list) and data:
            first = data[0] if isinstance(data[0], dict) else {}
            media_type = str(first.get("media_type") or "").strip().lower()
            typ = str(first.get("type") or "").strip().lower()
            if "video" in media_type or "video" in typ:
                return "video"
            if "photo" in media_type or "photo" in typ:
                return "image"
            if "album" in media_type or "album" in typ or "carousel" in typ:
                return "carousel"
            if "link" in typ:
                return "link"
    if "video" in status_type:
        return "video"
    if "photo" in status_type:
        return "image"
    if "link" in status_type:
        return "link"
    if status_type:
        return status_type
    return "unknown"


def _run_callback_server(redirect_uri: str, timeout_s: int = 180) -> dict[str, str]:
    parsed = urlparse(redirect_uri)
    if parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1"):
        raise RuntimeError(
            "META_TEST_REDIRECT_URI doit être un callback local HTTP (ex: http://localhost:8768/callback)."
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

        # Le callback doit pointer sur le path attendu.
        callback_path = _OAuthCallbackHandler.callback_path
        if expected_path and callback_path != expected_path:
            raise RuntimeError(
                f"Callback inattendu: {callback_path!r} (attendu: {expected_path!r})."
            )
        if payload.get("code"):
            return payload
        raise RuntimeError("Callback reçu mais code manquant.")
    finally:
        server.shutdown()
        server.server_close()


async def _main() -> None:
    redirect_uri = (
        os.getenv("META_TEST_REDIRECT_URI") or "http://localhost:8768/callback"
    ).strip()
    limit = int(os.getenv("FACEBOOK_EXTRACT_LIMIT") or "10")
    comments_limit = int(os.getenv("FACEBOOK_COMMENTS_LIMIT") or "100")
    reactions_limit = int(os.getenv("FACEBOOK_REACTIONS_LIMIT") or "100")
    oauth_timeout_s = int(os.getenv("META_TEST_OAUTH_TIMEOUT_S") or "240")
    force_connect = (os.getenv("FACEBOOK_FORCE_CONNECT_EVERY_RUN") or "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )
    existing_page_token = (os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN") or "").strip()
    existing_page_id = (os.getenv("FACEBOOK_PAGE_ID") or "").strip()

    if not FACEBOOK_APP_ID or not FACEBOOK_APP_SECRET:
        raise RuntimeError("FACEBOOK_APP_ID / FACEBOOK_APP_SECRET manquants dans .env")

    extra_scopes = [
        "pages_manage_metadata",
        "pages_read_user_content",
    ]
    scopes = list(dict.fromkeys([*META_DEFAULT_SCOPES, *extra_scopes]))

    def choose_page(pages: list[dict]) -> dict:
        print("\nPages disponibles:", flush=True)
        for idx, p in enumerate(pages, start=1):
            print(f"  {idx}. {p.get('name')} (id={p.get('id')})", flush=True)
        print("  m. saisir un PAGE_ID manuellement", flush=True)
        while True:
            raw = input("\nChoisis le numero de page a extraire: ").strip()
            if raw.lower() == "m":
                manual_id = input("PAGE_ID: ").strip()
                matched = next((p for p in pages if str(p.get("id")) == manual_id), None)
                if matched:
                    return matched
                print("Ce PAGE_ID n'est pas dans la liste OAuth actuelle.", flush=True)
                continue
            try:
                n = int(raw)
                if 1 <= n <= len(pages):
                    return pages[n - 1]
            except Exception:
                pass
            print("Choix invalide. Reessaye.", flush=True)

    async def run_oauth_flow() -> tuple[dict, str, str]:
        state = secrets.token_urlsafe(16)
        oauth_url = build_meta_login_url(
            app_id=FACEBOOK_APP_ID,
            redirect_uri=redirect_uri,
            scopes=scopes,
            state=state,
        )

        print("\nCONNECT Facebook (ouverture navigateur):\n", flush=True)
        print(oauth_url, flush=True)
        print(
            f"\nAttente du callback OAuth... (timeout {oauth_timeout_s}s)\n",
            flush=True,
        )
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
        return page, str(page["id"]), str(page["access_token"])

    page = {"id": existing_page_id, "name": "from_env"}
    page_id = existing_page_id
    page_token = existing_page_token
    used_env_token = bool(page_token and page_id) and not force_connect

    if force_connect:
        print("Mode force connect actif: OAuth interactif a chaque execution.", flush=True)
        page, page_id, page_token = await run_oauth_flow()
    elif used_env_token:
        print("Using FACEBOOK_PAGE_ID + FACEBOOK_PAGE_ACCESS_TOKEN from .env", flush=True)
    else:
        page, page_id, page_token = await run_oauth_flow()

    collector = MetaCollector()
    account_ref = {
        "platform": "facebook",
        "page_access_token": page_token,
        "facebook_page_id": page_id,
    }
    posts_fields_min = "id,message,created_time,permalink_url"
    posts_fields_feed = (
        "id,message,story,created_time,permalink_url,status_type,"
        "full_picture,attachments{media_type,type,url,target,media}"
    )

    def _has_post_like_content(item: dict) -> bool:
        return bool(
            (item.get("message") or "").strip()
            or item.get("attachments")
            or item.get("full_picture")
            or (item.get("story") or "").strip()
        )

    def _is_system_story(item: dict) -> bool:
        story_text = str(item.get("story") or "").lower()
        return (
            "a changé sa photo de profil" in story_text
            or "a changé sa photo de couverture" in story_text
        )

    async def fetch_page_posts_with_fallback(token: str) -> list[dict]:
        # On combine plusieurs endpoints pour maximiser les chances d'obtenir
        # les publications réelles de la page selon le type de contenu.
        candidates: list[tuple[str, str, int, int, str]] = [
            (
                "published_posts",
                f"{page_id}/published_posts",
                min(limit, 100),
                max(limit * 3, 30),
                posts_fields_min,
            ),
            (
                "posts",
                f"{page_id}/posts",
                min(limit, 100),
                max(limit * 3, 30),
                posts_fields_min,
            ),
            (
                "feed",
                f"{page_id}/feed",
                min(max(limit * 3, 30), 100),
                max(limit * 6, 60),
                posts_fields_feed,
            ),
        ]

        merged: dict[str, dict] = {}
        source_counts: dict[str, int] = {}

        for source_name, source_path, req_limit, max_items, fields in candidates:
            rows = await _fetch_graph_collection(
                path=source_path,
                params={
                    "fields": fields,
                    "limit": req_limit,
                    "access_token": token,
                },
                max_items=max_items,
            )
            source_counts[source_name] = len(rows)
            for row in rows:
                if not isinstance(row, dict):
                    continue
                post_id = str(row.get("id") or "").strip()
                if not post_id:
                    continue
                if not _has_post_like_content(row):
                    continue
                if _is_system_story(row):
                    continue
                if post_id not in merged:
                    merged[post_id] = row

        ordered = sorted(
            merged.values(),
            key=lambda x: str(x.get("created_time") or ""),
            reverse=True,
        )
        posts_final = ordered[:limit]
        print(
            f"Sources posts: published_posts={source_counts.get('published_posts', 0)}, "
            f"posts={source_counts.get('posts', 0)}, feed={source_counts.get('feed', 0)} "
            f"=> selected={len(posts_final)}",
            flush=True,
        )
        return posts_final

    try:
        posts = await fetch_page_posts_with_fallback(page_token)
    except MetaGraphError as e:
        if used_env_token:
            print(
                "Env page token lacks required permissions; switching to interactive OAuth...",
                flush=True,
            )
            page, page_id, page_token = await run_oauth_flow()
            account_ref = {
                "platform": "facebook",
                "page_access_token": page_token,
                "facebook_page_id": page_id,
            }
            posts = await fetch_page_posts_with_fallback(page_token)
        else:
            raise RuntimeError(f"Facebook extraction failed after OAuth: {e}") from e

    page_metrics = await _safe_graph_get(
        page_id,
        {
            "fields": "id,name,category,link,fan_count,followers_count,verification_status",
            "access_token": page_token,
        },
    )
    page_insights_data, page_insights_debug = await _fetch_insights_metrics_debug(
        object_id=page_id,
        metrics=FACEBOOK_PAGE_INSIGHT_METRICS,
        access_token=page_token,
        period="day",
    )

    posts_detailed: list[dict] = []
    aggregate_post_reach = 0
    aggregate_post_impressions = 0
    aggregate_post_likes = 0
    aggregate_post_comments = 0
    aggregate_post_shares = 0
    aggregate_post_interactions = 0
    reach_known_count = 0
    impressions_known_count = 0
    total_posts = len(posts)
    for post_idx, post in enumerate(posts, start=1):
        post_id = str(post.get("id") or "").strip()
        if not post_id:
            continue
        print(
            f"[facebook] processing post {post_idx}/{total_posts}: {post_id}",
            flush=True,
        )

        metrics: dict | None = None
        comments: list[dict] | None = None
        post_insights: list[dict] | None = None
        reactions: list[dict] | None = None

        try:
            metrics = await collector.fetch_post_metrics(account_ref, post_id)
        except Exception:
            metrics = None

        comments = await _fetch_graph_collection(
            path=f"{post_id}/comments",
            params={
                "fields": (
                    "id,from{id,name},message,created_time,"
                    "like_count,comment_count,permalink_url,attachment"
                ),
                "limit": min(comments_limit, 100),
                "access_token": page_token,
            },
            max_items=comments_limit,
        )
        if not comments:
            comments = None

        post_insights, post_insights_debug = await _fetch_insights_metrics_debug(
            object_id=post_id,
            metrics=FACEBOOK_POST_INSIGHT_METRICS,
            access_token=page_token,
        )

        reactions = await _fetch_graph_collection(
            path=f"{post_id}/reactions",
            params={
                "fields": "id,name,type",
                "limit": min(reactions_limit, 100),
                "access_token": page_token,
            },
            max_items=reactions_limit,
        )
        if not reactions:
            reactions = None

        reactions_count = int(
            ((metrics or {}).get("reactions") or {}).get("summary", {}).get("total_count") or 0
        )
        comments_count = int(
            ((metrics or {}).get("comments") or {}).get("summary", {}).get("total_count") or 0
        )
        shares_count = int((((metrics or {}).get("shares") or {}).get("count") or 0))
        interactions_total = reactions_count + comments_count + shares_count
        post_reach = _extract_insight_value(post_insights, "post_impressions_unique")
        post_impressions = _extract_insight_value(post_insights, "post_impressions")

        if post_reach is not None:
            aggregate_post_reach += post_reach
            reach_known_count += 1
        if post_impressions is not None:
            aggregate_post_impressions += post_impressions
            impressions_known_count += 1
        aggregate_post_likes += reactions_count
        aggregate_post_comments += comments_count
        aggregate_post_shares += shares_count
        aggregate_post_interactions += interactions_total

        posts_detailed.append(
            {
                "post": post,
                "post_type_api": _facebook_post_type_api(post),
                "metrics": metrics,
                "post_insights": post_insights,
                "post_insights_debug": post_insights_debug,
                "comments": comments,
                "reactions": reactions,
                "comments_count_fetched": (
                    len([c for c in comments if isinstance(c, dict) and c.get("id")])
                    if comments
                    else None
                ),
                "reactions_count_fetched": (
                    len([r for r in reactions if isinstance(r, dict) and r.get("id")])
                    if reactions
                    else None
                ),
                "interactions": {
                    "reactions_count": reactions_count,
                    "comments_count": comments_count,
                    "shares_count": shares_count,
                    "interactions_total": interactions_total,
                    "reach": post_reach,
                    "impressions": post_impressions,
                },
            }
        )

    page_followers = int((page_metrics or {}).get("followers_count") or 0)
    page_likes = int((page_metrics or {}).get("fan_count") or 0)
    page_reach_daily = _extract_insight_value(page_insights_data, "page_impressions_unique")
    page_impressions_daily = _extract_insight_value(page_insights_data, "page_impressions")
    page_post_engagements_daily = _extract_insight_value(page_insights_data, "page_post_engagements")

    out = {
        "platform": "facebook",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "page": {"id": page_id, "name": page.get("name")},
        "page_metrics": page_metrics,
        "page_insights": page_insights_data,
        "page_insights_debug": page_insights_debug,
        "page_social": {
            "followers_count": page_followers or None,
            "likes_count": page_likes or None,
            "reach_daily": page_reach_daily,
            "impressions_daily": page_impressions_daily,
            "post_engagements_daily": page_post_engagements_daily,
        },
        "posts_count": len(posts),
        "posts": posts,
        "posts_detailed": posts_detailed,
        "posts_social_totals": {
            "likes_count": aggregate_post_likes,
            "comments_count": aggregate_post_comments,
            "shares_count": aggregate_post_shares,
            "interactions_total": aggregate_post_interactions,
            "reach_total_known_posts": aggregate_post_reach if reach_known_count else None,
            "impressions_total_known_posts": (
                aggregate_post_impressions if impressions_known_count else None
            ),
            "reach_known_posts_count": reach_known_count,
            "impressions_known_posts_count": impressions_known_count,
        },
        "extract_config": {
            "posts_limit": limit,
            "comments_limit_per_post": comments_limit,
            "reactions_limit_per_post": reactions_limit,
            "null_when_unavailable": True,
        },
        "api_base": BASE,
    }
    out_dir = ROOT / "scripts" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "facebook_extract_result.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nExtraction terminee.", flush=True)
    print(f"JSON enregistre: {out_path}\n", flush=True)


if __name__ == "__main__":
    asyncio.run(_main())

