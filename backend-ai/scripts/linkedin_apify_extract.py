from __future__ import annotations

import asyncio
import json
import os
import re
import secrets
import sys
import threading
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
load_dotenv(ROOT.parent / ".env")

from config.social_publish_config import (
    LINKEDIN_CLIENT_ID,
    LINKEDIN_CLIENT_SECRET,
    LINKEDIN_REDIRECT_URI,
    LINKEDIN_SCOPE,
)
from tools.social_publishing.linkedin_client import (
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
        q = parse_qs(parsed.query or "")
        code = (q.get("code") or [""])[0]
        state = (q.get("state") or [""])[0]
        error = (q.get("error_description") or q.get("error") or [""])[0]

        if code or error:
            _OAuthCallbackHandler.payload = {"code": code, "state": state, "error": error}
            if _OAuthCallbackHandler.done_event:
                _OAuthCallbackHandler.done_event.set()

        body = (
            "<html><body><h3>Connexion LinkedIn reçue.</h3>"
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
    host = parsed.hostname or "localhost"
    port = parsed.port or 80
    expected_path = parsed.path or "/"

    done = threading.Event()
    _OAuthCallbackHandler.payload = {}
    _OAuthCallbackHandler.done_event = done

    server = HTTPServer((host, port), _OAuthCallbackHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        if not done.wait(timeout=timeout_s):
            raise RuntimeError("Timeout OAuth: callback non reçu")
        payload = _OAuthCallbackHandler.payload
        if payload.get("error"):
            raise RuntimeError(f"OAuth refusé: {payload['error']}")
        if _OAuthCallbackHandler.callback_path != expected_path:
            raise RuntimeError(
                f"Callback inattendu: {_OAuthCallbackHandler.callback_path!r} (attendu: {expected_path!r})"
            )
        if not payload.get("code"):
            raise RuntimeError("Code OAuth manquant")
        return payload
    finally:
        server.shutdown()
        server.server_close()


def _env(name: str, required: bool = True) -> str:
    value = (os.getenv(name) or "").strip()
    if required and not value:
        raise RuntimeError(f"Missing {name} in .env")
    return value


ENV_PATH = ROOT.parent / ".env"


def _persist_env_var(name: str, value: str) -> bool:
    """Write or update KEY=value in .env. Returns True if written."""
    try:
        if not ENV_PATH.exists():
            ENV_PATH.write_text(f"{name}={value}\n", encoding="utf-8")
            os.environ[name] = value
            return True

        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
        new_lines: list[str] = []
        found = False
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith(f"{name}=") or stripped.startswith(f"{name} ="):
                new_lines.append(f"{name}={value}")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"{name}={value}")

        ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        os.environ[name] = value
        return True
    except Exception as exc:
        print(f"[warn] impossible d'ecrire {name} dans .env: {exc}", flush=True)
        return False


def _load_profile_map(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in data.items():
        if isinstance(k, str) and isinstance(v, str) and v.strip():
            out[k] = v.strip()
    return out


def _save_profile_map(path: Path, mapping: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")


def _try_extract_url_from_picture(profile: dict[str, Any]) -> str:
    """Some LinkedIn OIDC 'picture' URLs embed the public identifier. Best-effort only."""
    picture = str(profile.get("picture") or "").strip()
    if not picture:
        return ""
    # No reliable extraction; reserved for future heuristics.
    return ""


def _resolve_profile_url(
    *,
    access_token: str,
    profile: dict[str, Any],
) -> tuple[str, str]:
    """
    Retourne (profile_url, source).
    Stratégie stricte (sans fallback global) :
      1) cache -> linkedin_profile_map.json (par 'sub' du compte connecté)
      2) API   -> /v2/me vanityName (si le token le permet)
      3) sinon erreur explicite (pas de fallback .env global)
    """
    sub = str(profile.get("sub") or "").strip()
    if not sub:
        raise RuntimeError(
            "Impossible d'identifier le compte LinkedIn connecté (sub manquant). "
            "URL profil non résolue par sécurité."
        )

    map_file = ROOT / "scripts" / "results" / "linkedin_profile_map.json"
    mapping = _load_profile_map(map_file)
    if sub and sub in mapping:
        url = mapping[sub]
        return url, "cache"

    # 2) Try /rest/identityMe (r_profile_basicinfo -> basicInfo.profileUrl)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    identity_url = "https://api.linkedin.com/rest/identityMe"
    identity_headers = {
        **headers,
        "Linkedin-Version": "202510",
        "Accept": "application/json",
    }
    try:
        r_identity = requests.get(identity_url, headers=identity_headers, timeout=30)
        if r_identity.status_code == 200:
            identity = r_identity.json() if r_identity.content else {}
            basic = identity.get("basicInfo") if isinstance(identity, dict) else {}
            if not isinstance(basic, dict):
                basic = {}
            profile_url = str(
                basic.get("profileUrl")
                or identity.get("profileUrl")
                or ""
            ).strip()
            if profile_url:
                mapping[sub] = profile_url
                _save_profile_map(map_file, mapping)
                print(f"[auto] URL profil resolue via /rest/identityMe: {profile_url}", flush=True)
                return profile_url, "linkedin_identity"
        else:
            print(
                f"[info] /rest/identityMe non disponible (HTTP {r_identity.status_code}). "
                "Vérifie que le scope r_profile_basicinfo est bien demandé et accordé.",
                flush=True,
            )
    except Exception as exc:
        print(f"[info] /rest/identityMe erreur reseau: {exc}", flush=True)

    # 3) Try /v2/me vanityName (legacy path on some apps/scopes)
    me_url = "https://api.linkedin.com/v2/me"
    params = {"projection": "(id,vanityName,localizedFirstName,localizedLastName)"}
    try:
        r = requests.get(me_url, headers=headers, params=params, timeout=30)
        if r.status_code == 200:
            me = r.json() if r.content else {}
            vanity = str(me.get("vanityName") or "").strip()
            if vanity:
                url = f"https://www.linkedin.com/in/{vanity}/"
                if sub:
                    mapping[sub] = url
                    _save_profile_map(map_file, mapping)
                print(f"[auto] URL profil resolue via /v2/me: {url}", flush=True)
                return url, "linkedin_api"
        else:
            print(
                f"[info] /v2/me non disponible (HTTP {r.status_code}). "
                "L'app LinkedIn n'a pas l'accès profil requis, ou le scope n'est pas accordé.",
                flush=True,
            )
    except Exception as exc:
        print(f"[info] /v2/me erreur reseau: {exc}", flush=True)

    # 4) One-time manual fallback bound to the connected account (sub).
    print(
        "\n"
        "================ ACTION REQUISE (une seule fois) ================\n"
        "Impossible de resoudre automatiquement l'URL profil pour ce compte.\n"
        "Colle une seule fois l'URL publique du compte CONNECTE.\n"
        "Cette URL sera enregistree uniquement dans linkedin_profile_map.json\n"
        "pour le sub OAuth courant (aucun fallback global).\n"
        "Exemple: https://www.linkedin.com/in/ton-identifiant/\n"
        "=================================================================\n",
        flush=True,
    )
    while True:
        raw = input("LinkedIn Profile URL (compte connecté): ").strip()
        if raw.startswith("https://www.linkedin.com/in/"):
            mapping[sub] = raw
            _save_profile_map(map_file, mapping)
            print(
                "[ok] URL profil enregistree pour ce compte. "
                "Les prochains lancements seront automatiques pour ce meme compte.",
                flush=True,
            )
            return raw, "manual_per_sub"
        print("URL invalide. Doit commencer par https://www.linkedin.com/in/", flush=True)


def _normalize_actor_id(actor_id: str) -> str:
    """
    Apify REST API requires '~' instead of '/' in actor IDs.
    Ex: 'harvestapi/linkedin-profile-posts' -> 'harvestapi~linkedin-profile-posts'
    """
    return actor_id.strip().replace("/", "~")


def _resolve_manual_profile_url() -> tuple[str, str]:
    """
    Résout l'URL profil LinkedIn sans OAuth.
    Priorité:
      1) argument CLI: python linkedin_apify_extract.py <profile_url>
      2) env LINKEDIN_PROFILE_URL_INPUT
      3) prompt terminal
    """
    cli_value = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    env_value = _env("LINKEDIN_PROFILE_URL_INPUT", required=False)
    candidate = cli_value or env_value
    source = "cli_arg" if cli_value else ("env_input" if env_value else "prompt")

    while True:
        if not candidate:
            candidate = input("LinkedIn Profile URL: ").strip()
            source = "prompt"
        if candidate.startswith("https://www.linkedin.com/in/"):
            return candidate, source
        print("URL invalide. Doit commencer par https://www.linkedin.com/in/", flush=True)
        candidate = ""


def _run_actor(token: str, actor_id: str, run_input: dict[str, Any]) -> str:
    safe_id = _normalize_actor_id(actor_id)
    url = f"https://api.apify.com/v2/acts/{safe_id}/run-sync-get-dataset-items"
    params = {"token": token, "format": "json", "clean": "true"}
    r = requests.post(url, params=params, json=run_input, timeout=600)
    if r.status_code >= 300:
        try:
            body = r.json()
        except Exception:
            body = r.text[:1000]
        raise RuntimeError(f"Apify actor run failed: HTTP {r.status_code} | {body}")

    # run-sync-get-dataset-items returns the dataset items directly
    try:
        data = r.json()
    except Exception:
        data = []
    # We piggyback: return the items encoded as JSON string via a sentinel key.
    # But to keep a clean interface, cache items on function attribute.
    _run_actor._last_items = data if isinstance(data, list) else []  # type: ignore[attr-defined]
    # Return a synthetic dataset id placeholder since items are already fetched.
    return "__inline__"


def _read_dataset_items(token: str, dataset_id: str, limit: int) -> list[dict[str, Any]]:
    # If we used run-sync, items are already cached on _run_actor.
    if dataset_id == "__inline__":
        cached = getattr(_run_actor, "_last_items", [])
        return [x for x in (cached or []) if isinstance(x, dict)][:limit]

    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
    params = {
        "token": token,
        "format": "json",
        "clean": "true",
        "limit": str(limit),
        "desc": "true",
    }
    r = requests.get(url, params=params, timeout=120)
    if r.status_code >= 300:
        raise RuntimeError(f"Apify dataset read failed: HTTP {r.status_code} | {r.text[:1000]}")
    data = r.json() if r.content else []
    if not isinstance(data, list):
        return []
    return [x for x in data if isinstance(x, dict)]


def _normalize_posts(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    posts: list[dict[str, Any]] = []
    for item in items[:limit]:
        raw_type = str(item.get("type") or "").strip().lower()
        post_type_api = raw_type if raw_type else "unknown"
        posts.append(
            {
                "id": item.get("id") or item.get("postId"),
                "post_type_api": post_type_api,
                "text": item.get("text") or item.get("content") or item.get("postText"),
                "published_at": item.get("postedAt") or item.get("timestamp") or item.get("date"),
                "post_url": item.get("postUrl") or item.get("url"),
                "likes": item.get("likes") or item.get("numLikes"),
                "comments": item.get("comments") or item.get("numComments"),
                "reposts": item.get("reposts") or item.get("numShares") or item.get("shares"),
                "raw": item,
            }
        )
    return posts


def _parse_count_like(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if not isinstance(value, str):
        return None

    raw = value.strip().lower().replace(",", "").replace(" ", "")
    if not raw:
        return None
    # examples: "3200", "+3k", "3.2k"
    m = re.match(r"^\+?(\d+(?:\.\d+)?)([km]?)$", raw)
    if not m:
        return None
    num = float(m.group(1))
    suffix = m.group(2)
    if suffix == "k":
        num *= 1_000
    elif suffix == "m":
        num *= 1_000_000
    return int(num)


def _extract_profile_counters(items: list[dict[str, Any]]) -> dict[str, Any]:
    followers_keys = {
        "followers",
        "followersCount",
        "followerCount",
        "numFollowers",
        "subscriberCount",
        "subscribers",
    }
    connections_keys = {
        "connections",
        "connectionsCount",
        "connectionCount",
        "numConnections",
    }
    posts_keys = {
        "postsCount",
        "postCount",
        "totalPosts",
        "totalPostsCount",
        "numPosts",
    }

    counters: dict[str, tuple[int, str, str] | None] = {
        "followers_count": None,
        "connections_count": None,
        "total_posts_count": None,
    }

    def _set_counter(name: str, value: int, source: str, precision: str) -> None:
        current = counters.get(name)
        if current is None:
            counters[name] = (value, source, precision)
            return
        # Keep exact over estimated if both exist.
        if current[2] != "exact" and precision == "exact":
            counters[name] = (value, source, precision)

    # 1) Deep scan explicit fields from actor output.
    for item in items:
        stack: list[Any] = [item]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                for k, v in current.items():
                    parsed = _parse_count_like(v)
                    if parsed is not None:
                        if k in followers_keys:
                            exact = isinstance(v, (int, float)) or (
                                isinstance(v, str) and bool(re.search(r"\d{4,}", v.replace(",", "")))
                            )
                            _set_counter("followers_count", parsed, f"raw.{k}", "exact" if exact else "estimated")
                        elif k in connections_keys:
                            exact = isinstance(v, (int, float)) or (
                                isinstance(v, str) and bool(re.search(r"\d{3,}", v.replace(",", "")))
                            )
                            _set_counter("connections_count", parsed, f"raw.{k}", "exact" if exact else "estimated")
                        elif k in posts_keys:
                            exact = isinstance(v, (int, float)) or (
                                isinstance(v, str) and bool(re.search(r"\d+", v))
                            )
                            _set_counter("total_posts_count", parsed, f"raw.{k}", "exact" if exact else "estimated")
                    if isinstance(v, (dict, list)):
                        stack.append(v)
            elif isinstance(current, list):
                stack.extend(current)

    # 2) Text fallback for patterns like "3,786 relations", "3786 connections".
    for item in items:
        stack: list[Any] = [item]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                for _, v in current.items():
                    if isinstance(v, str):
                        low = v.lower()
                        m_conn = re.search(r"(\d[\d,\.\s]{1,12})\s*(relations|relation|connections?)", low)
                        if m_conn:
                            parsed = _parse_count_like(m_conn.group(1).replace(" ", ""))
                            if parsed is not None:
                                _set_counter("connections_count", parsed, "raw.text_pattern_connections", "exact")

                        m_follow = re.search(r"(\d[\d,\.\s]{1,12})\s*(followers?|abonn[ée]s?)", low)
                        if m_follow:
                            parsed = _parse_count_like(m_follow.group(1).replace(" ", ""))
                            if parsed is not None:
                                _set_counter("followers_count", parsed, "raw.text_pattern_followers", "exact")

                        m_posts = re.search(r"(\d[\d,\.\s]{1,12})\s*(posts?|publications?)", low)
                        if m_posts:
                            parsed = _parse_count_like(m_posts.group(1).replace(" ", ""))
                            if parsed is not None:
                                _set_counter("total_posts_count", parsed, "raw.text_pattern_posts", "exact")

                    if isinstance(v, (dict, list)):
                        stack.append(v)
            elif isinstance(current, list):
                stack.extend(current)

    # 3) Final fallback from headline shorthand, only if missing.
    for item in items:
        author = item.get("author")
        if isinstance(author, dict):
            info = author.get("info")
            if isinstance(info, str):
                m = re.search(r"\+?\d+(?:\.\d+)?[kKmM]", info)
                if m:
                    parsed = _parse_count_like(m.group(0))
                    if parsed is not None and counters["followers_count"] is None:
                        _set_counter("followers_count", parsed, "author.info_heuristic", "estimated")

    def _export(name: str) -> tuple[int | None, str, str]:
        value = counters.get(name)
        if value is None:
            return None, "not_available", "unknown"
        return value

    followers_count, followers_source, followers_precision = _export("followers_count")
    connections_count, connections_source, connections_precision = _export("connections_count")
    total_posts_count, total_posts_source, total_posts_precision = _export("total_posts_count")

    return {
        "followers_count": followers_count,
        "followers_count_source": followers_source,
        "followers_count_precision": followers_precision,
        "connections_count": connections_count,
        "connections_count_source": connections_source,
        "connections_count_precision": connections_precision,
        "total_posts_count": total_posts_count,
        "total_posts_count_source": total_posts_source,
        "total_posts_count_precision": total_posts_precision,
    }


async def _oauth_profile() -> tuple[dict[str, Any], str]:
    redirect_uri = (
        os.getenv("LINKEDIN_TEST_REDIRECT_URI")
        or LINKEDIN_REDIRECT_URI
        or "http://localhost:8769/callback"
    ).strip()
    oauth_timeout_s = int(_env("LINKEDIN_OAUTH_TIMEOUT_S", required=False) or "240")

    if not LINKEDIN_CLIENT_ID or not LINKEDIN_CLIENT_SECRET:
        raise RuntimeError("Missing LINKEDIN_CLIENT_ID / LINKEDIN_CLIENT_SECRET")

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
    if (payload.get("state") or "") != state:
        raise RuntimeError("State OAuth invalide")

    access_token = await exchange_linkedin_code(
        code=payload.get("code") or "",
        client_id=LINKEDIN_CLIENT_ID,
        client_secret=LINKEDIN_CLIENT_SECRET,
        redirect_uri=redirect_uri,
    )
    profile = await linkedin_userinfo(access_token)
    return profile, access_token


def main() -> None:
    token = _env("APIFY_TOKEN")
    actor_id = _env("APIFY_LINKEDIN_ACTOR_ID")
    limit = int(_env("LINKEDIN_EXTRACT_LIMIT", required=False) or "10")
    profile_url, url_source = _resolve_manual_profile_url()

    # Generic input compatible with most LinkedIn profile actors.
    run_input = {
        "profileUrls": [profile_url],
        "maxPosts": limit,
        "maxItems": limit,
    }

    print(f"Running Apify actor: {actor_id}")
    print(f"Profile URL: {profile_url}  (source: {url_source})")
    dataset_id = _run_actor(token, actor_id, run_input)
    print(f"Apify dataset id: {dataset_id}")

    items = _read_dataset_items(token, dataset_id, limit=limit)
    posts = _normalize_posts(items, limit=limit)
    profile_counters = _extract_profile_counters(items)

    out = {
        "platform": "linkedin",
        "source": "apify",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "profile": {},
        "profile_url": profile_url,
        "profile_social": profile_counters,
        "posts_count": len(posts),
        "posts": posts,
        "extract_config": {
            "limit": limit,
            "actor_id": actor_id,
            "dataset_id": dataset_id,
            "profile_url_source": url_source,
            "profile_url_auto_resolved": False,
        },
    }

    out_dir = ROOT / "scripts" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "linkedin_extract_result.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nExtraction complete. JSON saved: {out_path}")


if __name__ == "__main__":
    main()

