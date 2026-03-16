 
# backend-ai/guardrails/safety_checks.py
# Messages de refus — un par catégorie détectée par le LLM

REFUSAL_MESSAGES = {
    "fraud":   "Ce projet semble viser à tromper des personnes. BrandAI accompagne uniquement des projets honnêtes.",
    "illegal": "Ce projet implique des activités illégales. BrandAI ne peut pas vous accompagner.",
    "harmful": "Ce projet pourrait causer du tort. BrandAI ne peut pas vous accompagner.",
    "default": "Ce projet ne respecte pas les conditions d'utilisation de BrandAI.",
}

def get_refusal_message(category: str) -> str:
    return REFUSAL_MESSAGES.get(category, REFUSAL_MESSAGES["default"])