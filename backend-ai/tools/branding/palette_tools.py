"""
Outils LangChain pour PaletteAgent (ReAct) : brouillon LLM + validation déterministe.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable

from config.branding_config import PALETTE_TARGET_COUNT
from prompts.branding.palette_prompt import (
    PALETTE_SYSTEM_PROMPT,
    build_palette_user_prompt,
)

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

# Description « pourquoi cette palette » (français attendu dans le prompt)
PALETTE_DESCRIPTION_MIN_LEN = 24


def parse_llm_json_object(raw: str) -> dict:
    """Parse une sortie modèle ; tolère fences markdown et texte autour."""
    if raw is None:
        raise json.JSONDecodeError("Invalid JSON (empty response)", "", 0)

    s = str(raw).strip()
    if not s:
        raise json.JSONDecodeError("Invalid JSON (empty response)", raw or "", 0)

    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", s, flags=re.IGNORECASE).strip()

    try:
        out = json.loads(cleaned)
        if isinstance(out, dict):
            return out
    except json.JSONDecodeError:
        pass

    brace_start = cleaned.find("{")
    if brace_start >= 0:
        depth = 0
        for i, ch in enumerate(cleaned[brace_start:], start=brace_start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        out = json.loads(cleaned[brace_start : i + 1])
                        if isinstance(out, dict):
                            return out
                    except json.JSONDecodeError:
                        break

    preview = (s[:120] + "…") if len(s) > 120 else s
    raise json.JSONDecodeError(f"Invalid JSON (no parseable object): {preview!r}", s, 0)


def _normalize_hex(h: str) -> str | None:
    t = (h or "").strip()
    if not t:
        return None
    if t.startswith("#") and len(t) == 7 and _HEX_RE.match(t):
        return t.upper()
    if len(t) == 6 and re.match(r"^[0-9A-Fa-f]{6}$", t):
        return "#" + t.upper()
    return None


def _normalize_swatches(raw: list) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("label") or "").strip()
        hx = _normalize_hex(str(item.get("hex") or item.get("color") or ""))
        if not name or not hx:
            continue
        role = str(item.get("role") or "accent").strip() or "accent"
        rationale = str(item.get("rationale") or item.get("description") or "").strip()
        out.append({"name": name, "hex": hx, "role": role, "rationale": rationale})
    return out


def normalize_palette_options(raw: list) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        pname = str(item.get("palette_name") or item.get("name") or "").strip()
        desc = str(
            item.get("palette_description")
            or item.get("why_palette")
            or "",
        ).strip()
        sw = _normalize_swatches(item.get("swatches") or item.get("colors") or [])
        if not pname or len(sw) < 2:
            continue
        out.append({
            "palette_name": pname,
            "palette_description": desc,
            "swatches": sw,
        })
    return out


def _hex_signature(palette: dict) -> frozenset[str]:
    sw = palette.get("swatches") or []
    hx = []
    for s in sw:
        if isinstance(s, dict) and s.get("hex"):
            hx.append(str(s["hex"]).upper())
    return frozenset(hx)


def _palettes_are_pairwise_distinct(options: list[dict[str, Any]]) -> bool:
    sigs = [_hex_signature(p) for p in options]
    return len(sigs) == len(set(sigs)) and all(len(s) >= 2 for s in sigs)


def make_draft_palettes_tool(
    llm,
    idea: dict,
    brand_name: str,
    *,
    target: int = PALETTE_TARGET_COUNT,
):
    @traceable(name="tool.draft_palettes", tags=["branding", "tool", "palette_draft"])
    def _draft(validation_feedback: str) -> str:
        user_prompt = build_palette_user_prompt(idea, brand_name, target=target)
        fb = (validation_feedback or "").strip()
        if fb:
            user_prompt += (
                "\n\n--- RETOUR DU VALIDATEUR (corrige et renvoie un JSON valide complet) ---\n"
                + fb
            )
        messages = [
            SystemMessage(content=PALETTE_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        response = llm.invoke(messages)
        content = response.content if response and getattr(response, "content", None) else ""
        return content if isinstance(content, str) else str(content)

    @tool
    def draft_palettes(validation_feedback: str = "") -> str:
        """
        Produit un brouillon JSON avec la clé « palette_options » (3 palettes) pour la marque.
        Premier appel : validation_feedback vide.
        Si validate_palettes renvoie une erreur, rappeler avec le message d'erreur dans validation_feedback.
        """
        return _draft(validation_feedback)

    return draft_palettes


def make_validate_palettes_tool(*, target: int = PALETTE_TARGET_COUNT):

    @traceable(name="tool.validate_palettes", tags=["branding", "tool", "palette_validate"])
    def _validate(palettes_json: str) -> str:
        try:
            data = parse_llm_json_object(palettes_json)
        except Exception as e:
            return json.dumps(
                {
                    "ok": False,
                    "error": f"JSON illisible ou invalide : {e}",
                    "validation_hints": "Renvoie un objet JSON unique avec la clé palette_options (tableau).",
                },
                ensure_ascii=False,
                indent=2,
            )

        raw_opts = data.get("palette_options")
        if raw_opts is None and isinstance(data.get("palettes"), list):
            raw_opts = data.get("palettes")
        if not isinstance(raw_opts, list):
            return json.dumps(
                {
                    "ok": False,
                    "error": "Clé « palette_options » manquante ou invalide.",
                    "validation_hints": "Le JSON doit contenir palette_options : [ {...}, ... ]",
                },
                ensure_ascii=False,
                indent=2,
            )

        options = normalize_palette_options(raw_opts)
        if len(options) < target:
            return json.dumps(
                {
                    "ok": False,
                    "error": (
                        f"Attendu {target} palettes exploitables, reçu {len(options)} "
                        "(nom + au moins 2 swatches hex valides par palette)."
                    ),
                    "validation_hints": "Complète ou corrige chaque palette (palette_name, palette_description, swatches).",
                },
                ensure_ascii=False,
                indent=2,
            )

        options = options[:target]

        for i, p in enumerate(options):
            desc = str(p.get("palette_description") or "").strip()
            if len(desc) < PALETTE_DESCRIPTION_MIN_LEN:
                return json.dumps(
                    {
                        "ok": False,
                        "error": (
                            f"Palette « {p.get('palette_name') or i + 1} » : "
                            f"« palette_description » doit expliquer le choix (au moins "
                            f"{PALETTE_DESCRIPTION_MIN_LEN} caractères)."
                        ),
                        "validation_hints": "Ajoute pour chaque palette un texte court en français : "
                        "pourquoi cette direction couleur colle au secteur / à la cible.",
                    },
                    ensure_ascii=False,
                    indent=2,
                )

        if not _palettes_are_pairwise_distinct(options):
            return json.dumps(
                {
                    "ok": False,
                    "error": "Les palettes ne sont pas assez distinctes (jeux de couleurs trop proches ou doublons).",
                    "validation_hints": "Change les hex pour que les 3 directions soient clairement différentes.",
                },
                ensure_ascii=False,
                indent=2,
            )

        return json.dumps(
            {"ok": True, "palette_options": options},
            ensure_ascii=False,
            indent=2,
        )

    @tool
    def validate_palettes(palettes_json: str) -> str:
        """
        Vérifie le JSON des palettes (sortie de draft_palettes) : structure, nombre,
        descriptions « pourquoi cette palette », couleurs distinctes entre les 3 propositions.
        """
        return _validate(palettes_json)

    return validate_palettes
