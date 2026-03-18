REFUSAL_MESSAGES = {
    "fraud":   "BrandAI ne peut pas vous accompagner dans ce projet. Il semble viser à tromper des personnes.",
    "illegal": "BrandAI ne peut pas vous accompagner dans ce projet. Il implique des activités illégales.",
    "harmful": "BrandAI ne peut pas vous accompagner dans ce projet. Il pourrait causer du tort.",
    "default": "BrandAI ne peut pas vous accompagner dans ce type de projet.",
}


def get_refusal_message(category: str) -> str:
    """
    Fallback uniquement — utilisé si le LLM échoue.
    En temps normal, c'est le LLM qui génère le message.
    """
    return REFUSAL_MESSAGES.get(category, REFUSAL_MESSAGES["default"])