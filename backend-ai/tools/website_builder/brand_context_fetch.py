"""
Phase 1 — Récupération du contexte projet (idée + brand kit complet).

Source unique : backend-api FastAPI (port 8000 par défaut).
- `GET /api/ideas/{id}`                       → idée + clarification
- `GET /api/branding/ideas/{id}/bundle`       → naming + slogan + palette + logo

Les deux requêtes sont exécutées en parallèle puis normalisées dans un
`BrandContext` typé et auto-suffisant pour Phase 2 / 3 / 4.
"""

from __future__ import annotations

import asyncio
import base64
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from config.website_builder_config import (
    BACKEND_API_BASE_URL,
    BACKEND_API_TIMEOUT_SECONDS,
    DEFAULT_BODY_FONT,
    DEFAULT_TITLE_FONT,
)

logger = logging.getLogger("brandai.website_builder.context")


# ─────────────────────────────────────────────────────────────────────────────
# DataClass : contexte normalisé consommé par les prompts
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class BrandContext:
    idea_id: int

    # Brief / idée
    project_name: str
    sector: str
    target_audience: str
    short_pitch: str
    description_brief: str
    language: str  # "fr" | "en"

    # Branding
    brand_name: str
    slogan: str
    logo_url: str | None

    # Palette (hex)
    primary_color: str
    secondary_color: str
    accent_color: str
    background_color: str
    surface_color: str
    text_color: str

    # Typography (peut venir du palette ou défaut)
    title_font: str
    body_font: str

    # Direction colorimétrique de la palette (ambiance des couleurs, PAS le style du site)
    palette_direction: str

    # Données brutes pour debug / fallback éventuel
    raw_palette: dict[str, Any] = field(default_factory=dict)
    raw_logo: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "idea_id": self.idea_id,
            "project_name": self.project_name,
            "sector": self.sector,
            "target_audience": self.target_audience,
            "short_pitch": self.short_pitch,
            "description_brief": self.description_brief,
            "language": self.language,
            "brand_name": self.brand_name,
            "slogan": self.slogan,
            "logo_url": self.logo_url,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "accent_color": self.accent_color,
            "background_color": self.background_color,
            "surface_color": self.surface_color,
            "text_color": self.text_color,
            "title_font": self.title_font,
            "body_font": self.body_font,
            "palette_direction": self.palette_direction,
            "raw_logo": self.raw_logo,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Appels HTTP backend-api
# ─────────────────────────────────────────────────────────────────────────────
async def _get_json(client: httpx.AsyncClient, url: str, headers: dict[str, str]) -> dict[str, Any]:
    resp = await client.get(url, headers=headers)
    resp.raise_for_status()
    if resp.status_code == 204 or not resp.content:
        return {}
    return resp.json() or {}


async def fetch_idea_row(idea_id: int, access_token: str) -> dict[str, Any]:
    url = f"{BACKEND_API_BASE_URL}/ideas/{idea_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=httpx.Timeout(BACKEND_API_TIMEOUT_SECONDS, connect=5.0)) as client:
        return await _get_json(client, url, headers)


async def fetch_branding_bundle(idea_id: int, access_token: str) -> dict[str, Any]:
    url = f"{BACKEND_API_BASE_URL}/branding/ideas/{idea_id}/bundle"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=httpx.Timeout(BACKEND_API_TIMEOUT_SECONDS, connect=5.0)) as client:
        return await _get_json(client, url, headers)


# ─────────────────────────────────────────────────────────────────────────────
# Extracteurs depuis blobs JSONB
# ─────────────────────────────────────────────────────────────────────────────
def _swatches_by_role(palette_chosen: dict[str, Any]) -> dict[str, str]:
    """Regroupe les swatches d'une palette choisie par leur rôle."""
    swatches = palette_chosen.get("swatches") or []
    out: dict[str, str] = {}
    for sw in swatches:
        if not isinstance(sw, dict):
            continue
        role = str(sw.get("role") or "").strip().lower()
        hex_value = str(sw.get("hex") or "").strip()
        if role and hex_value and role not in out:
            out[role] = hex_value
    return out


def _pick_color(roles: dict[str, str], *candidates: str, default: str) -> str:
    for r in candidates:
        v = roles.get(r)
        if v:
            return v
    return default


def _pick_http_url(obj: Any) -> str | None:
    if not isinstance(obj, dict):
        return None
    for key in ("image_url", "url", "primary_url", "cloudinary_url"):
        v = obj.get(key)
        if isinstance(v, str) and v.strip().startswith("http"):
            return v.strip()
    return None


def _variants_http_url(variants: Any) -> str | None:
    if not isinstance(variants, list):
        return None
    for variant in variants:
        if isinstance(variant, dict):
            got = _pick_http_url(variant)
            if got:
                return got
    return None


def _svg_to_data_url(svg_data: Any) -> str | None:
    if not isinstance(svg_data, str):
        return None
    svg = svg_data.strip()
    if not svg.startswith("<svg"):
        return None
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _logo_concepts_data_url(logo_concepts: Any) -> str | None:
    """
    Convertit le 1er concept logo (base64) en data URL.
    Format attendu (branding): generated.logo_concepts[0].image_base64 + image_mime
    """
    if not isinstance(logo_concepts, list) or not logo_concepts:
        return None
    c0 = logo_concepts[0]
    if not isinstance(c0, dict):
        return None

    # priorité version transparente si disponible
    b64 = c0.get("image_base64_transparent") or c0.get("image_base64")
    mime = c0.get("image_mime_transparent") or c0.get("image_mime") or "image/png"
    if isinstance(b64, str) and b64.strip():
        return f"data:{mime};base64,{b64.strip()}"
    return None


def _extract_logo_url(logo_row: dict[str, Any], logo_chosen: dict[str, Any]) -> str | None:
    """
    Cherche une URL exploitable dans plusieurs emplacements :
    1) logo.chosen.*            (cas nominal)
    2) logo.variants[*].*       (fallback courant)
    3) logo.generated[*].*      (fallback pipeline)
    4) logo.svg_data            (fallback data URL)
    """
    # 1) chosen
    got = _pick_http_url(logo_chosen)
    if got:
        return got
    got = _variants_http_url(logo_chosen.get("variants"))
    if got:
        return got

    # 2) row-level direct / variants
    got = _pick_http_url(logo_row)
    if got:
        return got
    got = _variants_http_url(logo_row.get("variants"))
    if got:
        return got

    # 3) generated list
    got = _variants_http_url(logo_row.get("generated"))
    if got:
        return got
    # 3-bis) generated object with logo_concepts (brand final preview format)
    generated = logo_row.get("generated")
    if isinstance(generated, dict):
        got = _logo_concepts_data_url(generated.get("logo_concepts"))
        if got:
            return got

    # 4) svg inline fallback
    got = _svg_to_data_url(logo_row.get("svg_data"))
    if got:
        return got
    return None


def _extract_visual_style(palette_chosen: dict[str, Any]) -> str:
    desc = str(palette_chosen.get("palette_description") or palette_chosen.get("palette_name") or "").strip()
    if not desc:
        return "moderne, élégant, professionnel"
    if len(desc) > 220:
        return desc[:217] + "…"
    return desc


# ─────────────────────────────────────────────────────────────────────────────
# Builder principal
# ─────────────────────────────────────────────────────────────────────────────
def _build_brand_context(idea: dict[str, Any], bundle: dict[str, Any]) -> BrandContext:
    naming = (bundle.get("naming") or {}) if isinstance(bundle, dict) else {}
    slogan = (bundle.get("slogan") or {}) if isinstance(bundle, dict) else {}
    palette = (bundle.get("palette") or {}) if isinstance(bundle, dict) else {}
    logo = (bundle.get("logo") or {}) if isinstance(bundle, dict) else {}

    palette_chosen = palette.get("chosen") if isinstance(palette.get("chosen"), dict) else {}
    logo_chosen = logo.get("chosen") if isinstance(logo.get("chosen"), dict) else {}

    roles = _swatches_by_role(palette_chosen or {})

    brand_name = (
        str(naming.get("chosen_name") or "").strip()
        or str(idea.get("name") or "").strip()
        or "Notre Marque"
    )

    return BrandContext(
        idea_id=int(idea.get("id") or 0),
        project_name=str(idea.get("name") or "").strip() or brand_name,
        sector=str(idea.get("clarity_sector") or idea.get("sector") or "").strip(),
        target_audience=str(
            idea.get("clarity_target_users") or idea.get("target_audience") or ""
        ).strip(),
        short_pitch=str(idea.get("clarity_short_pitch") or "").strip(),
        description_brief=str(idea.get("description") or idea.get("clarity_solution") or "").strip(),
        language=str(idea.get("clarity_language") or "fr").strip().lower() or "fr",
        brand_name=brand_name,
        slogan=str(slogan.get("chosen_slogan") or "").strip(),
        logo_url=_extract_logo_url(logo or {}, logo_chosen or {}),
        primary_color=_pick_color(roles, "primary", default="#111827"),
        secondary_color=_pick_color(roles, "secondary", default="#6B7280"),
        accent_color=_pick_color(roles, "accent", default="#F59E0B"),
        background_color=_pick_color(roles, "background", default="#FFFFFF"),
        surface_color=_pick_color(roles, "surface", "neutral", default="#F3F4F6"),
        text_color=_pick_color(roles, "text", default="#111827"),
        title_font=str(palette_chosen.get("title_font") or DEFAULT_TITLE_FONT).strip(),
        body_font=str(palette_chosen.get("body_font") or DEFAULT_BODY_FONT).strip(),
        palette_direction=_extract_visual_style(palette_chosen or {}),
        raw_palette=palette_chosen or {},
        raw_logo=logo_chosen or {},
    )


def validate_brand_context(ctx: BrandContext) -> None:
    """Garde-fou : si on n'a pas le minimum vital, on lève une erreur claire."""
    if not ctx.project_name:
        raise RuntimeError("Contexte invalide : project_name manquant.")
    if not ctx.description_brief and not ctx.short_pitch:
        raise RuntimeError(
            "Contexte invalide : ni description ni pitch — "
            "lance d'abord le clarifier pour cette idée."
        )
    for label, value in (
        ("primary_color", ctx.primary_color),
        ("background_color", ctx.background_color),
    ):
        if not (value.startswith("#") and len(value) == 7):
            raise RuntimeError(f"Contexte invalide : {label}={value!r} n'est pas un hex #RRGGBB.")


async def fetch_full_brand_context(idea_id: int, access_token: str) -> BrandContext:
    """Phase 1 : exécute idée + bundle en parallèle puis normalise."""
    logger.info("[website_builder] PHASE 1 (CONTEXT) START idea_id=%s", idea_id)
    idea, bundle = await asyncio.gather(
        fetch_idea_row(idea_id, access_token),
        fetch_branding_bundle(idea_id, access_token),
    )
    ctx = _build_brand_context(idea, bundle)
    validate_brand_context(ctx)
    logger.info(
        "[website_builder] PHASE 1 (CONTEXT) SUCCESS idea_id=%s brand=%s palette=%s/%s/%s",
        idea_id,
        ctx.brand_name,
        ctx.primary_color,
        ctx.secondary_color,
        ctx.accent_color,
    )
    return ctx
