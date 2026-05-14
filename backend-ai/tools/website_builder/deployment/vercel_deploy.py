"""
Phase 5 — Déploiement Vercel.

Workflow :
  1. POST   {VERCEL_API_BASE}/v13/deployments      → crée le déploiement
  2. GET    {VERCEL_API_BASE}/v13/deployments/{id} → polling jusqu'à READY / ERROR

Le HTML est envoyé en inline base64 (un seul fichier `index.html`), pas de build,
pas de framework. Vercel sert le fichier statique tel quel.

Ce module N'INVOQUE AUCUN LLM : c'est purement de l'I/O HTTP.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import re
import time
from dataclasses import dataclass
from typing import Any

import httpx

from config.website_builder_config import (
    VERCEL_API_BASE,
    VERCEL_API_KEY,
    VERCEL_HTTP_TIMEOUT_SECONDS,
    VERCEL_POLL_INTERVAL_SECONDS,
    VERCEL_POLL_TIMEOUT_SECONDS,
    VERCEL_PROJECT_NAME_PREFIX,
    VERCEL_TEAM_ID,
)

logger = logging.getLogger("brandai.website_builder.vercel")

# États finaux Vercel — voir https://vercel.com/docs/rest-api/endpoints/deployments
_READY_STATES_OK = {"READY"}
_READY_STATES_KO = {"ERROR", "CANCELED"}


# ─────────────────────────────────────────────────────────────────────────────
# Result type
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class VercelDeployment:
    deployment_id: str
    project_name: str
    url: str               # ex: brandai-42-abcd.vercel.app (sans schéma)
    full_url: str          # ex: https://brandai-42-abcd.vercel.app
    state: str             # READY / ERROR / ...
    ready: bool
    elapsed_seconds: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "deployment_id": self.deployment_id,
            "project_name": self.project_name,
            "url": self.url,
            "full_url": self.full_url,
            "state": self.state,
            "ready": self.ready,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _slugify_project_name(raw: str) -> str:
    """Vercel n'accepte que [a-z0-9-], 1..100 caractères, pas de '--' consécutifs."""
    s = (raw or "").strip().lower()
    s = re.sub(r"[^a-z0-9-]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    if not s:
        s = "brandai-site"
    return s[:100]


def build_project_name(idea_id: int, *, brand_name: str | None = None) -> str:
    base = f"{VERCEL_PROJECT_NAME_PREFIX}{idea_id}"
    if brand_name:
        base = f"{base}-{brand_name}"
    return _slugify_project_name(base)


def _auth_headers() -> dict[str, str]:
    if not VERCEL_API_KEY:
        raise RuntimeError(
            "VERCEL_API_KEY manquant dans .env — impossible de déployer sur Vercel."
        )
    return {
        "Authorization": f"Bearer {VERCEL_API_KEY}",
        "Content-Type": "application/json",
    }


def _query_params() -> dict[str, str]:
    if VERCEL_TEAM_ID:
        return {"teamId": VERCEL_TEAM_ID}
    return {}


def _build_create_payload(html: str, project_name: str) -> dict[str, Any]:
    """Crée le body pour POST /v13/deployments avec un index.html inline."""
    encoded = base64.b64encode(html.encode("utf-8")).decode("ascii")
    return {
        "name": project_name,
        "files": [
            {
                "file": "index.html",
                "data": encoded,
                "encoding": "base64",
            }
        ],
        "projectSettings": {
            "framework": None,
            "buildCommand": None,
            "outputDirectory": None,
            "installCommand": None,
            "devCommand": None,
        },
        "target": "production",
    }


def _normalize_url(raw: str | None) -> tuple[str, str]:
    """Retourne (url_sans_schema, url_complete_https) à partir d'un retour Vercel."""
    if not raw:
        return "", ""
    raw = str(raw).strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        full = raw
        bare = re.sub(r"^https?://", "", raw, count=1)
    else:
        bare = raw
        full = f"https://{raw}"
    return bare, full


# ─────────────────────────────────────────────────────────────────────────────
# Calls Vercel
# ─────────────────────────────────────────────────────────────────────────────
async def _create_deployment(client: httpx.AsyncClient, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{VERCEL_API_BASE}/v13/deployments"
    resp = await client.post(url, json=payload, params=_query_params(), headers=_auth_headers())
    if resp.status_code >= 400:
        try:
            err = resp.json()
        except Exception:
            err = {"raw": resp.text[:300]}
        raise RuntimeError(
            f"Vercel POST /v13/deployments {resp.status_code} : "
            f"{err.get('error', err)}"
        )
    return resp.json() or {}


async def _get_deployment(client: httpx.AsyncClient, deployment_id: str) -> dict[str, Any]:
    url = f"{VERCEL_API_BASE}/v13/deployments/{deployment_id}"
    resp = await client.get(url, params=_query_params(), headers=_auth_headers())
    if resp.status_code >= 400:
        try:
            err = resp.json()
        except Exception:
            err = {"raw": resp.text[:300]}
        raise RuntimeError(
            f"Vercel GET /v13/deployments/{deployment_id} {resp.status_code} : "
            f"{err.get('error', err)}"
        )
    return resp.json() or {}


async def _delete_deployment(client: httpx.AsyncClient, deployment_id: str) -> None:
    url = f"{VERCEL_API_BASE}/v13/deployments/{deployment_id}"
    resp = await client.delete(url, params=_query_params(), headers=_auth_headers())
    if resp.status_code >= 400:
        try:
            err = resp.json()
        except Exception:
            err = {"raw": resp.text[:300]}
        raise RuntimeError(
            f"Vercel DELETE /v13/deployments/{deployment_id} {resp.status_code} : "
            f"{err.get('error', err)}"
        )


async def _poll_until_ready(
    client: httpx.AsyncClient,
    deployment_id: str,
    *,
    started_at: float,
) -> dict[str, Any]:
    interval = max(0.5, VERCEL_POLL_INTERVAL_SECONDS)
    deadline = started_at + VERCEL_POLL_TIMEOUT_SECONDS

    while True:
        data = await _get_deployment(client, deployment_id)
        state = str(data.get("readyState") or data.get("status") or "").upper()
        logger.info(
            "[website_builder] Vercel poll deployment_id=%s state=%s",
            deployment_id,
            state or "(unknown)",
        )

        if state in _READY_STATES_OK:
            return data
        if state in _READY_STATES_KO:
            err_msg = data.get("errorMessage") or data.get("error") or state
            raise RuntimeError(f"Vercel deployment échoué (state={state}) : {err_msg}")

        if time.monotonic() > deadline:
            raise TimeoutError(
                f"Vercel deployment {deployment_id} pas READY après "
                f"{VERCEL_POLL_TIMEOUT_SECONDS:.0f}s (state={state})."
            )

        await asyncio.sleep(interval)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
async def deploy_html_to_vercel(
    *,
    html: str,
    idea_id: int,
    brand_name: str | None = None,
) -> VercelDeployment:
    """Crée un déploiement Vercel à partir d'un HTML statique et attend READY."""
    if not html or "<html" not in html.lower():
        raise ValueError("html invalide : impossible de déployer.")

    project_name = build_project_name(idea_id, brand_name=brand_name)
    payload = _build_create_payload(html, project_name)
    started_at = time.monotonic()

    logger.info(
        "[website_builder] PHASE 5 (DEPLOYMENT) START idea_id=%s project=%s html_len=%d",
        idea_id,
        project_name,
        len(html),
    )

    timeout = httpx.Timeout(VERCEL_HTTP_TIMEOUT_SECONDS, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        created = await _create_deployment(client, payload)
        deployment_id = str(created.get("id") or "").strip()
        if not deployment_id:
            raise RuntimeError(f"Réponse Vercel sans id : {created}")
        final = await _poll_until_ready(client, deployment_id, started_at=started_at)

    elapsed = time.monotonic() - started_at

    # Priorité : alias[0] si présent (URL plus jolie type {project}.vercel.app), sinon url.
    raw_alias = final.get("alias")
    alias_first = raw_alias[0] if isinstance(raw_alias, list) and raw_alias else None
    bare_url, full_url = _normalize_url(alias_first or final.get("url"))
    state = str(final.get("readyState") or final.get("status") or "").upper()

    result = VercelDeployment(
        deployment_id=deployment_id,
        project_name=project_name,
        url=bare_url,
        full_url=full_url,
        state=state,
        ready=state in _READY_STATES_OK,
        elapsed_seconds=elapsed,
    )

    logger.info(
        "[website_builder] PHASE 5 (DEPLOYMENT) SUCCESS idea_id=%s project=%s url=%s elapsed=%.2fs",
        idea_id,
        project_name,
        result.full_url or "(unknown)",
        elapsed,
    )
    return result


async def delete_vercel_deployment(*, deployment_id: str) -> None:
    """Supprime un deploiement Vercel existant."""
    dep_id = str(deployment_id or "").strip()
    if not dep_id:
        raise ValueError("deployment_id manquant pour suppression.")
    timeout = httpx.Timeout(VERCEL_HTTP_TIMEOUT_SECONDS, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        await _delete_deployment(client, dep_id)
