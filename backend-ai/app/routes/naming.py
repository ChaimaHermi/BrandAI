"""
Génération de noms (Naming) avec préférences utilisateur one-shot — sans persistance des prefs.
Charge le contexte clarifié via backend-api, exécute NameAgent, optionnellement persiste name_options.
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
from agents.branding.name_agent import NameAgent
from app.routes.pipeline import _persist_brand_identity_row

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Naming"])


class StyleTonIn(BaseModel):
    brand_values: list[str] = Field(default_factory=list)
    personality: list[str] = Field(default_factory=list)
    user_feelings: list[str] = Field(default_factory=list)


class ConstraintsIn(BaseModel):
    name_language: str = "fr"
    name_length: str = "medium"
    include_keywords: str = ""
    exclude_keywords: str = ""


class NamingGenerateRequest(BaseModel):
    idea_id: int
    style_ton: StyleTonIn = Field(default_factory=StyleTonIn)
    constraints: ConstraintsIn = Field(default_factory=ConstraintsIn)
    user_remarks: str = Field(
        default="",
        description="Remarques libres (régénération) pour affiner le brief.",
    )
    access_token: str = Field(..., description="JWT utilisateur pour GET /ideas/{id} et persistance")
    persist: bool = True


class NamingGenerateResponse(BaseModel):
    idea_id: int
    status: str
    name_options: list[dict[str, Any]] = Field(default_factory=list)
    branding_status: str | None = None
    name_error: str | None = None
    agent_errors: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    persisted: bool = False


def _prefs_from_body(body: NamingGenerateRequest) -> dict[str, Any]:
    return {
        "brand_values": list(body.style_ton.brand_values or []),
        "personality": list(body.style_ton.personality or []),
        "user_feelings": list(body.style_ton.user_feelings or []),
        "name_language": body.constraints.name_language or "",
        "name_length": body.constraints.name_length or "",
        "include_keywords": body.constraints.include_keywords or "",
        "exclude_keywords": body.constraints.exclude_keywords or "",
        "user_remarks": (body.user_remarks or "").strip(),
    }


def _idea_api_to_clarified(row: dict) -> dict[str, Any]:
    """Mappe la réponse GET /api/ideas/{id} vers clarified_idea attendu par NameAgent."""
    ta = row.get("target_audience") or ""
    return {
        "idea_name": (row.get("name") or "").strip(),
        "sector": (row.get("clarity_sector") or row.get("sector") or "").strip(),
        "target_users": (row.get("clarity_target_users") or ta or "").strip(),
        "problem": (row.get("clarity_problem") or "").strip(),
        "solution_description": (
            (row.get("clarity_solution") or row.get("description") or "").strip()
        ),
        "country": (row.get("clarity_country") or "").strip() or "Non précisé",
        "country_code": (row.get("clarity_country_code") or "TN").strip(),
        "language": (row.get("clarity_language") or "fr").strip(),
        "short_pitch": row.get("clarity_short_pitch"),
    }


async def _fetch_idea_row(idea_id: int, access_token: str) -> dict:
    base = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/api").rstrip("/")
    url = f"{base}/ideas/{idea_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Idée introuvable")
        if resp.status_code == 401:
            raise HTTPException(status_code=401, detail="Non authentifié")
        if not resp.is_success:
            raise HTTPException(
                status_code=502,
                detail=f"backend-api ideas: {resp.status_code} {resp.text[:200]}",
            )
        return resp.json()


@router.post("/naming/generate", response_model=NamingGenerateResponse)
async def naming_generate(body: NamingGenerateRequest) -> NamingGenerateResponse:
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
    st.naming_preferences = _prefs_from_body(body)

    agent = NameAgent()
    st = await agent.run(st)

    bi = st.brand_identity or {}
    name_options = bi.get("name_options") or []
    if not isinstance(name_options, list):
        name_options = []

    out = NamingGenerateResponse(
        idea_id=body.idea_id,
        status=st.status,
        name_options=name_options,
        branding_status=bi.get("branding_status"),
        name_error=bi.get("name_error"),
        agent_errors=dict(bi.get("agent_errors") or {}),
        errors=list(st.errors or []),
    )

    if (
        body.persist
        and name_options
        and st.status == "name_generated"
        and body.access_token
    ):
        try:
            started_at = datetime.now(timezone.utc)
            completed_at = datetime.now(timezone.utc)
            await _persist_brand_identity_row(
                idea_id=body.idea_id,
                brand_identity=bi,
                started_at=started_at,
                completed_at=completed_at,
                access_token=body.access_token,
            )
            out.persisted = True
        except Exception as e:
            logger.exception("Échec persistance brand_identity après naming")
            out.errors = list(out.errors) + [f"persist: {e}"]

    return out
