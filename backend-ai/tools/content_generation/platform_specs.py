"""Règles techniques par plateforme (get_platform_spec) — données réelles, pas de LLM."""

from __future__ import annotations

from typing import Any

# Limites indicatives (APIs évoluent — à ajuster si besoin)
PLATFORM_SPECS: dict[str, dict[str, Any]] = {
    "instagram": {
        "platform": "instagram",
        "max_caption_chars": 2200,
        "recommended_caption_chars": 125,
        "image_ratio": "1:1",
        "image_width": 1080,
        "image_height": 1080,
        "hashtags_max": 30,
        "notes": "Feed carré ou vertical ; éviter le texte illisible sur mobile.",
    },
    "facebook": {
        "platform": "facebook",
        "max_caption_chars": 63206,
        "recommended_caption_chars": 500,
        "image_ratio": "1.91:1",
        "image_width": 1200,
        "image_height": 628,
        "notes": "Posts page ; image optionnelle.",
    },
    "linkedin": {
        "platform": "linkedin",
        "max_caption_chars": 3000,
        "recommended_caption_chars": 1500,
        "image_ratio": "1.91:1",
        "image_width": 1200,
        "image_height": 627,
        "notes": "Ton professionnel ; pas de hashtags en masse.",
    },
}


def get_spec_for_platform(platform: str) -> dict[str, Any]:
    p = (platform or "").strip().lower()
    if p not in PLATFORM_SPECS:
        raise ValueError(f"Plateforme inconnue : {platform}")
    return dict(PLATFORM_SPECS[p])
