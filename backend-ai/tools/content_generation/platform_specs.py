"""Règles techniques par plateforme (get_platform_spec) — données réelles, pas de LLM."""

from __future__ import annotations

from typing import Any

PLATFORM_SPECS: dict[str, dict[str, Any]] = {
    "instagram": {
        "platform": "instagram",
        "max_caption_chars": 2200,
        "recommended_caption_chars": 500,   # 125 = portion visible avant "...plus" — PAS la longueur cible
        "visible_before_cutoff": 125,        # info séparée, ne pas utiliser comme cible de longueur
        "image_ratio": "1:1",
        "image_width": 1080,
        "image_height": 1080,
        "hashtags_max": 30,
        "notes": (
            "Hook ≤ 125 caractères visible avant coupure mobile. "
            "Corps du post : 300 à 700 caractères recommandés. "
            "Hashtags regroupés en bas si demandés."
        ),
    },
    "facebook": {
        "platform": "facebook",
        "max_caption_chars": 63206,
        "recommended_caption_chars": 450,   # 300–600 = zone d'engagement optimal
        "image_ratio": "1.91:1",
        "image_width": 1200,
        "image_height": 628,
        "notes": (
            "Format optimal : 300 à 600 caractères. "
            "Question d'engagement en fin de post si pas de CTA. "
            "Aucun hashtag."
        ),
    },
    "linkedin": {
        "platform": "linkedin",
        "max_caption_chars": 3000,
        "recommended_caption_chars": 1500,  # 1200–1800 = zone de performance LinkedIn
        "image_ratio": "1.91:1",
        "image_width": 1200,
        "image_height": 627,
        "notes": (
            "Hook ≤ 90 caractères visible avant 'voir plus'. "
            "Paragraphes courts, beaucoup d'espace. "
            "3 à 5 hashtags pros toujours en fin de post."
        ),
    },
}


def get_spec_for_platform(platform: str) -> dict[str, Any]:
    p = (platform or "").strip().lower()
    if p not in PLATFORM_SPECS:
        raise ValueError(f"Plateforme inconnue : {platform}")
    return dict(PLATFORM_SPECS[p])