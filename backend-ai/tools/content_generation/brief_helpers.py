"""
Règles métier partagées sur le brief (ex. quand générer une image).
"""

from __future__ import annotations

from typing import Any


def should_include_image_in_post(platform: str, brief: dict[str, Any]) -> bool:
    """
    Aligné sur le front : Instagram inclut une image par défaut (sauf si désactivé) ;
    Facebook / LinkedIn : image seulement si l’utilisateur l’a demandée.
    """
    inc = brief.get("include_image")
    if platform == "instagram":
        return inc is not False
    return inc is True
