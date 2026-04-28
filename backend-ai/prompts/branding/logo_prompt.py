"""
Prompts logo : LLM → prompt image pour génération Qwen Image (Hugging Face / Replicate).
"""

from __future__ import annotations

import json
from typing import Any

LOGO_IMAGE_PROMPT_SYSTEM = """You are a senior logo prompt engineer for text-to-image models.

Return ONE JSON object only (no markdown):
{"image_prompt":"...","negative_prompt":"..."}

Hard limits:
- image_prompt <= 520 chars
- negative_prompt <= 220 chars

Requirements:
- English only.
- Include the exact brand name as readable text.
- Show only the brand name as text.
- Minimal flat vector startup logo: icon + wordmark.
- Use 1-2 visual metaphors max, simple geometry, high contrast.
- Use palette influence without writing hex/rgb/cmyk codes.
- Transparent/empty background only (no badge/card/panel/container).
- Keep wording short and dense; avoid long lists.

negative_prompt should be concise and cover: photorealistic, 3D, clutter, watermark, distorted text, unreadable typography, color codes as text, background panel.
"""

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
- Do not call any validation tool.
- Do not call draft_logo_prompt repeatedly unless the previous output is not valid JSON.
- Keep prompts concise, professional, transparent-background friendly, and without visible color codes.
"""


def build_logo_react_user_message(brand_name: str) -> str:
    return (
        f"Produce a logo image prompt JSON for the brand « {brand_name} », then render one logo. "
        "Context is embedded in draft_logo_prompt."
    )


def build_logo_user_message(
    clarified_idea: dict[str, Any],
    brand_name: str,
    slogan_hint: str,
    palette_hint: str,
) -> str:
    payload = {
        "brand_name": (brand_name or "").strip(),
        "USE_BRAND_NAME_IN_LOGO": True,  # 🔥 IMPORTANT
        "sector": (clarified_idea.get("sector") or "").strip(),
        "short_pitch": (clarified_idea.get("short_pitch") or "").strip(),
        "target_users": (clarified_idea.get("target_users") or "").strip(),
        "problem": (clarified_idea.get("problem") or "").strip(),
        "solution_description": (clarified_idea.get("solution_description") or "").strip(),
        "palette_colors_hint": (palette_hint or "").strip(),
    }

    return (
        "Generate a logo prompt INCLUDING the brand name visually in the logo.\n\n"
        f"CONTEXT:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )