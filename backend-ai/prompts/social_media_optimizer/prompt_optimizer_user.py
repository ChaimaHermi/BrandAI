"""User prompt builder for Social Media Optimizer."""

from __future__ import annotations

import json
from typing import Any


def build_optimizer_user_prompt(
    *,
    platform: str,
    project_context: dict[str, Any],
    stats: dict[str, Any],
) -> str:
    kpis_only = (stats or {}).get("kpis") or {}
    return (
        f"Plateforme demandee: {platform}\n\n"
        "Contexte projet:\n"
        f"{json.dumps(project_context, ensure_ascii=False, indent=2)}\n\n"
        "KPIs de travail (ne pas les recopier dans la sortie):\n"
        f"{json.dumps(kpis_only, ensure_ascii=False, indent=2)}\n\n"
        "Top posts:\n"
        f"{json.dumps((stats or {}).get('top_posts') or [], ensure_ascii=False, indent=2)}\n\n"
        "Repartition reactions:\n"
        f"{json.dumps((stats or {}).get('reactions_breakdown') or {}, ensure_ascii=False, indent=2)}\n\n"
        "Timeline engagement:\n"
        f"{json.dumps((stats or {}).get('evolution') or [], ensure_ascii=False, indent=2)}\n\n"
        "Instructions:\n"
        "- Utilise uniquement ces donnees.\n"
        "- N'invente pas de chiffres.\n"
        "- N'affiche pas les metriques absentes.\n"
        "- Donne maximum 5 recommandations.\n"
        "- Retourne uniquement un objet JSON valide."
    )

