"""
Génération de palettes de couleurs : idée clarifiée + nom de marque + préférences.
Fusionne avec le dernier brand_identity si présent.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field

from agents.base_agent import PipelineState
from agents.branding.palette_agent import PaletteAgent
from app.routes.naming import _fetch_idea_row, _idea_api_to_clarified
from app.routes.pipeline import _persist_brand_identity_row

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Palette"])


class PalettePreferencesIn(BaseModel):
    ambiance: str = ""
    style_couleur: list[str] = Field(default_factory=list)
    contraste: str = ""
    couleurs_eviter: str = ""
    user_remarks: str = ""


class PaletteGenerateRequest(BaseModel):
    idea_id: int
    brand_name: str = Field(..., min_length=1)
    preferences: PalettePreferencesIn = Field(default_factory=PalettePreferencesIn)
    slogan_hint: str = ""
    access_token: str
    persist: bool = True


class PaletteGenerateResponse(BaseModel):
    idea_id: int
    status: str
    palette_options: list[dict[str, Any]] = Field(default_factory=list)
    color_palette: dict[str, Any] = Field(default_factory=dict)
    branding_status: str | None = None
    palette_error: str | None = None
    errors: list[str] = Field(default_factory=list)
    persisted: bool = False


def _prefs_dict(p: PalettePreferencesIn) -> dict[str, Any]:
    return {
        "ambiance": p.ambiance or "",
        "style_couleur": list(p.style_couleur or []),
        "contraste": p.contraste or "",
        "couleurs_eviter": (p.couleurs_eviter or "").strip(),
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


@router.post("/palette/generate", response_model=PaletteGenerateResponse)
async def palette_generate(body: PaletteGenerateRequest) -> PaletteGenerateResponse:
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
    st.palette_preferences = _prefs_dict(body.preferences)
    st.palette_slogan_hint = (body.slogan_hint or "").strip()

    agent = PaletteAgent()
    st = await agent.run(st)
    bi = st.brand_identity or {}
    palettes = bi.get("palette_options") or []
    color_palette = bi.get("color_palette") if isinstance(bi.get("color_palette"), dict) else {}

    out = PaletteGenerateResponse(
        idea_id=body.idea_id,
        status=st.status,
        palette_options=palettes if isinstance(palettes, list) else [],
        color_palette=color_palette,
        branding_status=bi.get("branding_status"),
        palette_error=bi.get("palette_error"),
        errors=list(st.errors or []),
    )

    if (
        body.persist
        and out.palette_options
        and st.status == "palette_generated"
        and body.access_token
    ):
        try:
            prev = await _fetch_latest_brand_result_json(body.idea_id, body.access_token)
            merged: dict[str, Any] = dict(prev) if prev else {}
            merged["palette_options"] = out.palette_options
            merged["color_palette"] = out.color_palette
            merged["chosen_brand_name"] = merged.get("chosen_brand_name") or body.brand_name.strip()
            ae = dict(merged.get("agent_errors") or {})
            if bi.get("agent_errors"):
                ae.update(bi["agent_errors"])
            merged["agent_errors"] = ae
            if merged.get("name_options") or merged.get("slogan_options"):
                merged["branding_status"] = "partial"
            else:
                merged["branding_status"] = "palette_generated"

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
            logger.exception("Échec persistance brand_identity après palette")
            out.errors = list(out.errors) + [f"persist: {e}"]

    return out
