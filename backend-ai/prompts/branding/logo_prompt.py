"""
Prompt logo : génère un logo avec le nom de marque (wordmark + icon).
Pas de slogan dans le logo.
Le LLM produit un JSON {image_prompt, negative_prompt} pour un modèle text-to-image.
Chaîne image : HF Qwen → NVIDIA flux.2-klein-4b → Pollinations.
"""

from __future__ import annotations

import json
from typing import Any


LOGO_IMAGE_PROMPT_SYSTEM_WITH_NAME = """You are a creative brand identity designer specializing in logo prompts for text-to-image models (Flux, Qwen Image).

Return ONE JSON object only — no markdown, no explanation:
{"image_prompt":"...","negative_prompt":"..."}

⚠️ CHARACTER LIMITS — STRICT:
- image_prompt: MAXIMUM 460 characters. Count before responding. Never exceed.
- negative_prompt: MAXIMUM 220 characters.

=== YOUR CREATIVE MISSION ===

Design a logo icon that VISUALLY TELLS the story of the brand.
The icon must instantly communicate what the business does — like a visual shortcut to the product or service.

Think like a designer who has read the full project brief:
- Sportswear e-commerce → a stylized athletic sneaker or jersey silhouette
- Food delivery app → a scooter with a delivery bag
- Education platform → an open book with a spark
- Travel agency → a minimalist airplane or compass
- Fitness app → a bold dumbbell or running figure
- Medical clinic → a clean stethoscope
- Coffee shop → a steaming cup with creative twist

The icon must be:
✓ A simplified, flat-vector version of a REAL object tied to the business
✓ Instantly readable — someone glancing for 1 second understands the sector
✓ Clean and minimal — simplified silhouette, not detailed illustration
✓ Original — find a fresh angle on the object (unusual perspective, clever negative space, stylized proportions)


=== BRAND NAME SPELLING — CRITICAL ===
The brand name MUST appear EXACTLY as given — letter by letter, no variation allowed.
Write it verbatim in the prompt: if the name is "Sportella", write "Sportella" not "Sportela" or "Sportella".
To reinforce correct spelling, write the name twice in the image_prompt:
  once in the icon description context, once in the wordmark instruction.

=== IMAGE PROMPT STRUCTURE ===
minimal flat vector logo, [creative icon tied to business], the exact text '[X]' as bold wordmark spelling '[X]' letter by letter, [color 1] and [color 2], icon [left of / above] wordmark, transparent background, no fill, no shadow

=== NEGATIVE PROMPT ===
photorealistic, 3D render, gradient background, solid background, white background, colored background, drop shadow, outer glow, watermark, blurry, distorted text, illegible font, slogan, tagline, badge frame, decorative border, clipart, hex color codes.
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
    letters = " – ".join(list(brand_name))
    return (
        f"Generate a logo prompt for the brand « {brand_name} ».\n"
        f"EXACT SPELLING (letter by letter): {letters}\n"
        f"The wordmark must render this exact spelling: {brand_name}\n"
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
