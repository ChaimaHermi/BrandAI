"""
Prompt logo : génère un logo avec le nom de marque (wordmark + icon).
Pas de slogan dans le logo.
Le LLM produit un JSON {image_prompt, negative_prompt} pour un modèle text-to-image.
Chaîne image : HF Qwen → NVIDIA flux.2-klein-4b → Pollinations.
"""

from __future__ import annotations

import json
from typing import Any


LOGO_IMAGE_PROMPT_SYSTEM_WITH_NAME = """You are a senior logo prompt engineer for text-to-image models.

Return ONE JSON object only (no markdown):
{"image_prompt":"...","negative_prompt":"..."}

Hard limits:
- image_prompt <= 520 chars
- negative_prompt <= 220 chars

Requirements:
- English only.
- The logo MUST include the brand name as clearly readable text in the wordmark.
- Minimal flat vector logo: simple icon/symbol + brand name text.
- Use 1-2 visual metaphors relevant to the sector, clean geometry, high contrast.
- Use ONLY the brand palette colors provided in the context. Describe colors by NAME only (e.g., "dark green", "coral", "cream"), NOT by hex codes.
- Transparent/empty background only.
- Keep wording short and dense.
- No slogan, no tagline — only icon + brand name.

negative_prompt must cover: photorealistic, 3D, clutter, watermark, distorted text, unreadable typography, background panel, slogan, tagline, decorative borders, hex codes, color codes.
"""

# Alias utilisé par logo_tools.py (compat)
LOGO_IMAGE_PROMPT_SYSTEM = LOGO_IMAGE_PROMPT_SYSTEM_WITH_NAME

LOGO_REACT_SYSTEM_PROMPT = """You are a senior logo prompt engineer agent.

Goal:
1) Draft a professional JSON prompt for logo text-to-image.
2) Render exactly one logo image.

Tools:
- draft_logo_prompt(validation_feedback): returns JSON with keys image_prompt and negative_prompt.
- render_logo_image(image_prompt, negative_prompt): renders logo from the drafted prompt.

Sequence (STRICT):
1) Call draft_logo_prompt("") once.
2) Parse the returned JSON and call render_logo_image with the same values.
3) Return a short confirmation in French.

Rules:
- Do not call draft_logo_prompt repeatedly unless the previous output is not valid JSON.
- No slogan or tagline in the logo prompt.
- Transparent background, readable brand name.
"""


def build_logo_user_message_with_name(
    clarified_idea: dict[str, Any],
    brand_name: str,
    palette_hint: str,
) -> str:
    payload = {
        "brand_name": (brand_name or "").strip(),
        "INCLUDE_BRAND_NAME_AS_TEXT": True,
        "sector": (clarified_idea.get("sector") or "").strip(),
        "short_pitch": (clarified_idea.get("short_pitch") or "").strip(),
        "target_users": (clarified_idea.get("target_users") or "").strip(),
        "problem": (clarified_idea.get("problem") or "").strip(),
        "solution_description": (clarified_idea.get("solution_description") or "").strip(),
        "country": (clarified_idea.get("country") or "").strip(),
        "language": (clarified_idea.get("language") or "fr").strip(),
        "palette_colors_hint": (palette_hint or "").strip(),
    }
    return (
        f"Generate a logo prompt that includes the brand name « {brand_name} » as readable text (wordmark + icon).\n"
        "No slogan, no tagline.\n\n"
        f"CONTEXT:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


# Alias de compatibilité
def build_logo_user_message(
    clarified_idea: dict[str, Any],
    brand_name: str,
    slogan_hint: str,  # ignoré
    palette_hint: str,
) -> str:
    return build_logo_user_message_with_name(clarified_idea, brand_name, palette_hint)


def build_logo_react_user_message(
    brand_name: str,
    clarified_idea: dict[str, Any] | None = None,
    **kwargs,
) -> str:
    sector = (clarified_idea or {}).get("sector", "")
    pitch  = (clarified_idea or {}).get("short_pitch", "")
    return (
        f"Produce a logo prompt JSON for brand « {brand_name} » (icon + wordmark, no slogan). "
        f"Sector: {sector}. Pitch: {pitch}. Context embedded in draft_logo_prompt."
    )
