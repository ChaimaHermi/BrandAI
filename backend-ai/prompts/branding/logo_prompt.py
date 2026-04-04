"""
Prompts pour l’agent logo : le LLM rédige uniquement un prompt adapté aux modèles image (FLUX, Pollinations, etc.).
"""

from __future__ import annotations

import json
from typing import Any

LOGO_IMAGE_PROMPT_SYSTEM = """You are an expert at writing concise image generation prompts for logo / brand mark models.

Rules:
- Output MUST be a single JSON object only, no markdown fences, no commentary.
- Keys: "image_prompt" (string, English), "negative_prompt" (string, English, can be empty).
- The image_prompt describes ONLY the visual: subject, style, composition, lighting, background. Optimized for diffusion models (comma-separated phrases are OK).
- Brand context may be in French or English; translate visual instructions to English in image_prompt.
- Always require: professional logo mark or iconic symbol, centered composition, clean readable silhouette, suitable for app icon.
- Unless the user explicitly asks for wordmark, use: no text, no letters, no watermark, no signature.
- Prefer: flat vector look OR clean minimal symbol — avoid photorealistic stock photo unless the brief demands it.
- If brand colors are provided, weave them naturally (e.g. "primary color deep blue #1a2b3c").
- Keep image_prompt under ~1200 characters. negative_prompt under ~400 characters.

JSON shape example:
{"image_prompt":"...","negative_prompt":"..."}
"""


def build_logo_user_message(
    clarified_idea: dict[str, Any],
    brand_name: str,
    slogan_hint: str,
    palette_hint: str,
) -> str:
    payload = {
        "brand_name": (brand_name or "").strip(),
        "slogan_or_tagline_hint": (slogan_hint or "").strip(),
        "sector": (clarified_idea.get("sector") or "").strip(),
        "short_pitch": (clarified_idea.get("short_pitch") or "").strip(),
        "target_users": (clarified_idea.get("target_users") or "").strip(),
        "problem": (clarified_idea.get("problem") or "").strip(),
        "solution_description": (clarified_idea.get("solution_description") or "").strip(),
        "palette_colors_hint": (palette_hint or "").strip(),
    }
    return (
        "Produce the JSON object for image generation.\n\n"
        f"CONTEXT:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
