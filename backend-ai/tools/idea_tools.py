 
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


def validate_idea_input(name: str, description: str, sector: str) -> list[str]:
    """
    Valide les champs obligatoires avant d'appeler le LLM.
    Retourne une liste d'erreurs — vide si tout est valide.

    Exemple :
        validate_idea_input("A", "court", "ecommerce")
        → ["Le nom doit contenir au moins 2 caractères.",
           "La description doit contenir au moins 20 caractères."]
    """
    errors: list[str] = []

    if not name or len(name.strip()) < 2:
        errors.append("Le nom du projet doit contenir au moins 2 caractères.")

    if not description or len(description.strip()) < 20:
        errors.append("La description doit contenir au moins 20 caractères.")

    if not sector or not sector.strip():
        errors.append("Le secteur est obligatoire.")

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