"""
Extraction LinkedIn via Apify — async, sans OAuth ni fichier.

`access_token` : jeton API Apify (`APIFY_TOKEN`).
`account_id`   : URL profil publique (`https://www.linkedin.com/in/.../`) ou
                 identifiant public (slug) du profil.

Configuration Apify : constantes ``DEFAULT_*`` ci-dessous ou variables
d'environnement / paramètre ``actor_id`` de ``extract_linkedin``.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from social_etl.extraction.linkedin_apify_normalize import (  # noqa: E402
    extract_linkedin_profile_counters,
    normalize_linkedin_apify_items,
)

# Défauts (surchargés par env ou par le JSON du pipeline)
DEFAULT_APIFY_ACTOR_ID = os.getenv("APIFY_LINKEDIN_ACTOR_ID", "").strip()
DEFAULT_APIFY_TIMEOUT_S = float(os.getenv("APIFY_REQUEST_TIMEOUT_S", "600"))


def _normalize_actor_id(actor_id: str) -> str:
    return actor_id.strip().replace("/", "~")


def _profile_url_from_account_id(account_id: str) -> str:
    raw = str(account_id).strip()
    if raw.startswith("https://www.linkedin.com/in/"):
        return raw if raw.endswith("/") else raw + "/"
    if raw.startswith("https://linkedin.com/in/"):
        return "https://www.linkedin.com/in/" + raw.split("/in/", 1)[-1].lstrip("/")
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    slug = raw.strip("/")
    return f"https://www.linkedin.com/in/{slug}/"


async def _apify_run_sync_get_items(
    *,
    apify_token: str,
    actor_id: str,
    run_input: dict[str, Any],
    timeout_s: float,
) -> list[dict[str, Any]]:
    safe_id = _normalize_actor_id(actor_id)
    url = f"https://api.apify.com/v2/acts/{safe_id}/run-sync-get-dataset-items"
    params = {"token": apify_token, "format": "json", "clean": "true"}
    async with httpx.AsyncClient(timeout=timeout_s) as client:
        r = await client.post(url, params=params, json=run_input)
    if r.status_code >= 300:
        try:
            body = r.json()
        except Exception:
            body = (r.text or "")[:1000]
        raise RuntimeError(f"Apify actor run failed: HTTP {r.status_code} | {body}")
    try:
        data = r.json()
    except Exception:
        data = []
    if not isinstance(data, list):
        return []
    return [x for x in data if isinstance(x, dict)]


async def extract_linkedin(
    access_token: str,
    account_id: str,
    *,
    limit: int = 10,
    actor_id: str | None = None,
    apify_timeout_s: float | None = None,
) -> dict[str, Any]:
    """
    Lance l'acteur Apify configuré et renvoie la même structure que
    l'ancien ``linkedin_extract_result.json``.

    ``actor_id`` : identifiant de l'acteur Apify ; défaut
    ``APIFY_LINKEDIN_ACTOR_ID`` ou constante ``DEFAULT_APIFY_ACTOR_ID``.
    """
    apify_token = str(access_token).strip()
    if not apify_token:
        raise ValueError("access_token (jeton Apify) est requis.")

    resolved_actor = (actor_id or DEFAULT_APIFY_ACTOR_ID or "").strip()
    if not resolved_actor:
        raise ValueError(
            "actor_id requis (config JSON ou argument), ou variable "
            "d'environnement APIFY_LINKEDIN_ACTOR_ID."
        )

    timeout = float(apify_timeout_s if apify_timeout_s is not None else DEFAULT_APIFY_TIMEOUT_S)
    profile_url = _profile_url_from_account_id(account_id)
    run_input: dict[str, Any] = {
        "profileUrls": [profile_url],
        "maxPosts": limit,
        "maxItems": limit,
    }

    items = await _apify_run_sync_get_items(
        apify_token=apify_token,
        actor_id=resolved_actor,
        run_input=run_input,
        timeout_s=timeout,
    )
    posts = normalize_linkedin_apify_items(items, limit=limit)
    profile_counters = extract_linkedin_profile_counters(items)

    return {
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
            "actor_id": resolved_actor,
            "dataset_id": "__inline__",
            "profile_url_source": "account_id",
            "profile_url_auto_resolved": False,
            "apify_timeout_s": timeout,
        },
    }
