"""
Génération de slogans : contexte projet (API idée) + nom choisi + préférences one-shot.
Fusionne avec le dernier brand_identity si présent (ex. name_options du naming).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.base_agent import PipelineState
from agents.branding.slogan_agent import SloganAgent
from app.routes.naming import _fetch_idea_row, _idea_api_to_clarified
from app.routes.pipeline import _persist_brand_identity_row

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Slogan"])


class SloganPreferencesIn(BaseModel):
    positionnement: str = ""
    style_ton_slogan: list[str] = Field(default_factory=list)
    message_usp: list[str] = Field(default_factory=list)
    format: list[str] = Field(default_factory=list)
    style_linguistique: list[str] = Field(default_factory=list)
    longueur: str = ""
    langue: str = ""
    mots_eviter: str = ""
    user_remarks: str = ""


class SloganGenerateRequest(BaseModel):
    idea_id: int
    brand_name: str = Field(..., min_length=1)
    preferences: SloganPreferencesIn = Field(default_factory=SloganPreferencesIn)
    access_token: str
    persist: bool = True


class SloganGenerateResponse(BaseModel):
    idea_id: int
    status: str
    slogan_options: list[dict[str, Any]] = Field(default_factory=list)
    branding_status: str | None = None
    slogan_error: str | None = None
    errors: list[str] = Field(default_factory=list)
    persisted: bool = False


def _prefs_dict(p: SloganPreferencesIn) -> dict[str, Any]:
    return {
        "positionnement": p.positionnement or "",
        "style_ton_slogan": list(p.style_ton_slogan or []),
        "message_usp": list(p.message_usp or []),
        "format": list(p.format or []),
        "style_linguistique": list(p.style_linguistique or []),
        "longueur": p.longueur or "",
        "langue": p.langue or "",
        "mots_eviter": (p.mots_eviter or "").strip(),
        "user_remarks": (p.user_remarks or "").strip(),
    }


async def _fetch_latest_brand_result_json(
    idea_id: int,
    access_token: str,
) -> dict[str, Any] | None:
    base = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/api").rstrip("/")
    url = f"{base}/brand-identity/{idea_id}/latest"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 404:
            return None
        if not resp.is_success:
            logger.warning("brand-identity latest %s: %s", resp.status_code, resp.text[:200])
            return None
        row = resp.json()
        rj = row.get("result_json")
        return rj if isinstance(rj, dict) else None


@router.post("/slogan/generate", response_model=SloganGenerateResponse)
async def slogan_generate(body: SloganGenerateRequest) -> SloganGenerateResponse:
    row = await _fetch_idea_row(body.idea_id, body.access_token.strip())
    clarified = _idea_api_to_clarified(row)

    st = PipelineState(
        idea_id=body.idea_id,
        name=clarified.get("idea_name") or row.get("name") or "",
        sector=clarified.get("sector") or "",
        description=(row.get("description") or "").strip(),
        target_audience=clarified.get("target_users") or "",
    )
    st.clarified_idea = clarified
    st.brand_name_chosen = body.brand_name.strip()
    st.slogan_preferences = _prefs_dict(body.preferences)

    agent = SloganAgent()
    st = await agent.run(st)
    bi = st.brand_identity or {}
    slogans = bi.get("slogan_options") or []

    out = SloganGenerateResponse(
        idea_id=body.idea_id,
        status=st.status,
        slogan_options=slogans if isinstance(slogans, list) else [],
        branding_status=bi.get("branding_status"),
        slogan_error=bi.get("slogan_error"),
        errors=list(st.errors or []),
    )

    if (
        body.persist
        and out.slogan_options
        and st.status == "slogan_generated"
        and body.access_token
    ):
        try:
            prev = await _fetch_latest_brand_result_json(body.idea_id, body.access_token)
            merged: dict[str, Any] = dict(prev) if prev else {}
            merged["slogan_options"] = out.slogan_options
            merged["chosen_brand_name"] = body.brand_name.strip()
            if merged.get("name_options"):
                merged["branding_status"] = "partial"
            else:
                merged["branding_status"] = "slogan_generated"
            ae = dict(merged.get("agent_errors") or {})
            if bi.get("agent_errors"):
                ae.update(bi["agent_errors"])
            merged["agent_errors"] = ae

            started_at = datetime.now(timezone.utc)
            completed_at = datetime.now(timezone.utc)
            await _persist_brand_identity_row(
                idea_id=body.idea_id,
                brand_identity=merged,
                started_at=started_at,
                completed_at=completed_at,
                access_token=body.access_token,
            )
            out.persisted = True
        except Exception as e:
            logger.exception("Échec persistance brand_identity après slogan")
            out.errors = list(out.errors) + [f"persist: {e}"]

    return out
