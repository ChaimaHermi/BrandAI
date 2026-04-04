"""
Service branding : charge le contexte depuis backend-api, délègue aux agents.
Les étapes suivantes peuvent résoudre nom / slogan depuis la base (GET branding).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException

from agents.base_agent import PipelineState
from agents.branding.name_agent import NameAgent
from agents.branding.palette_agent import PaletteAgent
from agents.branding.slogan_agent import SloganAgent
from app.routes.pipeline import _persist_brand_identity_row, fetch_branding_merged_generated

logger = logging.getLogger(__name__)


class BrandingService:
    """Délègue vers les agents naming / slogan / palette ; charge le contexte depuis l’API."""

    @staticmethod
    async def fetch_idea_row(idea_id: int, access_token: str) -> dict:
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

    @staticmethod
    def idea_api_to_clarified(row: dict) -> dict[str, Any]:
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

    @staticmethod
    async def fetch_branding_step(idea_id: int, access_token: str, step: str) -> dict | None:
        """GET /branding/ideas/{id}/{step} — step in naming|slogan|palette|logo."""
        base = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/api").rstrip("/")
        url = f"{base}/branding/ideas/{idea_id}/{step}"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
            r = await client.get(url, headers=headers)
            if r.status_code != 200:
                return None
            return r.json()

    @classmethod
    async def resolve_chosen_brand_name(
        cls,
        idea_id: int,
        access_token: str,
        explicit: str | None,
    ) -> str:
        """Nom explicite (body) ou `chosen_name` issu de l’étape naming en base."""
        name = (explicit or "").strip()
        if name:
            return name
        row = await cls.fetch_branding_step(idea_id, access_token, "naming")
        if row and row.get("chosen_name"):
            return str(row["chosen_name"]).strip()
        raise HTTPException(
            status_code=400,
            detail="Nom de marque requis : renseignez brand_name ou enregistrez un chosen_name (naming).",
        )

    @classmethod
    async def resolve_slogan_hint(
        cls,
        idea_id: int,
        access_token: str,
        explicit: str | None,
    ) -> str:
        """Indice slogan optionnel : body ou slogan choisi en base."""
        hint = (explicit or "").strip()
        if hint:
            return hint
        row = await cls.fetch_branding_step(idea_id, access_token, "slogan")
        if row and row.get("chosen_slogan"):
            return str(row["chosen_slogan"]).strip()
        return ""

    @classmethod
    def _base_state(cls, idea_id: int, row: dict, clarified: dict[str, Any]) -> PipelineState:
        return PipelineState(
            idea_id=idea_id,
            name=clarified.get("idea_name") or row.get("name") or "",
            sector=clarified.get("sector") or "",
            description=(row.get("description") or "").strip(),
            target_audience=clarified.get("target_users") or "",
        )

    @classmethod
    async def generate_naming(
        cls,
        *,
        idea_id: int,
        naming_preferences: dict[str, Any],
        access_token: str,
        persist: bool,
    ) -> dict[str, Any]:
        row = await cls.fetch_idea_row(idea_id, access_token.strip())
        clarified = cls.idea_api_to_clarified(row)
        st = cls._base_state(idea_id, row, clarified)
        st.clarified_idea = clarified
        st.naming_preferences = naming_preferences

        agent = NameAgent()
        st = await agent.run(st)
        bi = st.brand_identity or {}
        name_options = bi.get("name_options") or []
        if not isinstance(name_options, list):
            name_options = []

        out: dict[str, Any] = {
            "idea_id": idea_id,
            "status": st.status,
            "name_options": name_options,
            "branding_status": bi.get("branding_status"),
            "name_error": bi.get("name_error"),
            "agent_errors": dict(bi.get("agent_errors") or {}),
            "errors": list(st.errors or []),
            "persisted": False,
        }

        if (
            persist
            and name_options
            and st.status == "name_generated"
            and access_token
        ):
            try:
                started_at = datetime.now(timezone.utc)
                completed_at = datetime.now(timezone.utc)
                await _persist_brand_identity_row(
                    idea_id=idea_id,
                    brand_identity=bi,
                    started_at=started_at,
                    completed_at=completed_at,
                    access_token=access_token,
                )
                out["persisted"] = True
            except Exception as e:
                logger.exception("Échec persistance brand_identity après naming")
                out["errors"] = list(out["errors"]) + [f"persist: {e}"]

        return out

    @classmethod
    async def generate_slogan(
        cls,
        *,
        idea_id: int,
        brand_name: str | None,
        slogan_preferences: dict[str, Any],
        access_token: str,
        persist: bool,
    ) -> dict[str, Any]:
        resolved_name = await cls.resolve_chosen_brand_name(idea_id, access_token, brand_name)
        row = await cls.fetch_idea_row(idea_id, access_token.strip())
        clarified = cls.idea_api_to_clarified(row)
        st = cls._base_state(idea_id, row, clarified)
        st.clarified_idea = clarified
        st.brand_name_chosen = resolved_name
        st.slogan_preferences = slogan_preferences

        agent = SloganAgent()
        st = await agent.run(st)
        bi = st.brand_identity or {}
        slogans = bi.get("slogan_options") or []

        out: dict[str, Any] = {
            "idea_id": idea_id,
            "status": st.status,
            "slogan_options": slogans if isinstance(slogans, list) else [],
            "branding_status": bi.get("branding_status"),
            "slogan_error": bi.get("slogan_error"),
            "errors": list(st.errors or []),
            "persisted": False,
            "resolved_brand_name": resolved_name,
        }

        if (
            persist
            and out["slogan_options"]
            and st.status == "slogan_generated"
            and access_token
        ):
            try:
                prev = await fetch_branding_merged_generated(idea_id, access_token)
                merged: dict[str, Any] = dict(prev) if prev else {}
                merged["slogan_options"] = out["slogan_options"]
                merged["chosen_brand_name"] = resolved_name
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
                    idea_id=idea_id,
                    brand_identity=merged,
                    started_at=started_at,
                    completed_at=completed_at,
                    access_token=access_token,
                )
                out["persisted"] = True
            except Exception as e:
                logger.exception("Échec persistance brand_identity après slogan")
                out["errors"] = list(out["errors"]) + [f"persist: {e}"]

        return out

    @classmethod
    async def generate_palette(
        cls,
        *,
        idea_id: int,
        brand_name: str | None,
        palette_preferences: dict[str, Any],
        slogan_hint: str | None,
        access_token: str,
        persist: bool,
    ) -> dict[str, Any]:
        resolved_name = await cls.resolve_chosen_brand_name(idea_id, access_token, brand_name)
        resolved_slogan_hint = await cls.resolve_slogan_hint(
            idea_id, access_token, slogan_hint
        )
        row = await cls.fetch_idea_row(idea_id, access_token.strip())
        clarified = cls.idea_api_to_clarified(row)
        st = cls._base_state(idea_id, row, clarified)
        st.clarified_idea = clarified
        st.brand_name_chosen = resolved_name
        st.palette_preferences = palette_preferences
        st.palette_slogan_hint = resolved_slogan_hint

        agent = PaletteAgent()
        st = await agent.run(st)
        bi = st.brand_identity or {}
        palettes = bi.get("palette_options") or []
        color_palette = bi.get("color_palette") if isinstance(bi.get("color_palette"), dict) else {}

        out: dict[str, Any] = {
            "idea_id": idea_id,
            "status": st.status,
            "palette_options": palettes if isinstance(palettes, list) else [],
            "color_palette": color_palette,
            "branding_status": bi.get("branding_status"),
            "palette_error": bi.get("palette_error"),
            "errors": list(st.errors or []),
            "persisted": False,
            "resolved_brand_name": resolved_name,
            "resolved_slogan_hint": resolved_slogan_hint,
        }

        if (
            persist
            and out["palette_options"]
            and st.status == "palette_generated"
            and access_token
        ):
            try:
                prev = await fetch_branding_merged_generated(idea_id, access_token)
                merged: dict[str, Any] = dict(prev) if prev else {}
                merged["palette_options"] = out["palette_options"]
                merged["color_palette"] = out["color_palette"]
                merged["chosen_brand_name"] = merged.get("chosen_brand_name") or resolved_name
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
                    idea_id=idea_id,
                    brand_identity=merged,
                    started_at=started_at,
                    completed_at=completed_at,
                    access_token=access_token,
                )
                out["persisted"] = True
            except Exception as e:
                logger.exception("Échec persistance brand_identity après palette")
                out["errors"] = list(out["errors"]) + [f"persist: {e}"]

        return out
