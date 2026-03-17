 
# ══════════════════════════════════════════
#   backend-ai/tools/idea_tools.py
#   Helpers purs pour l'Idea Clarifier
#   Pas de logique LLM ici — fonctions utilitaires uniquement
# ══════════════════════════════════════════

# ── Mapping secteurs ──────────────────────────────────────────

SECTOR_LABELS: dict[str, str] = {
    "tech":         "Technologie / SaaS",
    "ecommerce":    "E-commerce",
    "sante":        "Santé / Medtech",
    "education":    "Éducation / Formation",
    "finance":      "Finance / Fintech",
    "alimentation": "Alimentation / Foodtech",
    "mode":         "Mode / Lifestyle",
    "autre":        "Autre",
}


def get_sector_label(sector: str) -> str:
    """Retourne le label lisible du secteur."""
    return SECTOR_LABELS.get(sector.lower().strip(), sector)


def validate_idea_input(
    name: str,
    description: str,
    sector: str,
) -> list[str]:
    """
    Validation approche B — description libre.
    name et sector sont optionnels.
    Le LLM détecte secteur depuis la description.
    Le Brand Identity Agent génère le nom plus tard.
    """
    errors = []

    if not description or len(description.strip()) < 10:
        errors.append(
            "La description doit contenir "
            "au moins 10 caractères."
        )

    return errors


def build_idea_summary(
    name: str,
    sector: str,
    description: str,
    target_audience: str = "",
) -> str:
    """
    Construit un résumé structuré de l'idée brute
    pour injection dans le prompt LLM du Clarifier.
    """
    sector_label = get_sector_label(sector)
    lines = [
        f"Nom du projet : {name}",
        f"Secteur       : {sector_label}",
    ]
    if target_audience and target_audience.strip():
        lines.append(f"Public cible  : {target_audience.strip()}")
    lines.append(f"\nDescription soumise par l'utilisateur :\n{description.strip()}")
    return "\n".join(lines)