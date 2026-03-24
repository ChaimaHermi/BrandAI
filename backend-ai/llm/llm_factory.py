# ══════════════════════════════════════════════════════════════
#  llm/llm_factory.py
#  Factory simple et propre
#  → Groq uniquement (GPT OSS + LLaMA possible)
# ══════════════════════════════════════════════════════════════

from langchain_groq import ChatGroq
from config.settings import GROQ_KEYS


# ─────────────────────────────────────────────
# GROQ CLIENTS (DYNAMIQUE)
# ─────────────────────────────────────────────
def create_groq_clients(model: str = None) -> list:
    """
    Crée des clients Groq.
    - Par défaut → LLaMA
    - Sinon → modèle passé (ex: GPT OSS)
    """
    clients = []

    # 🔥 modèle par défaut
    model_name = model if model else "llama3-70b-8192"

    for key in GROQ_KEYS:
        clients.append(
            ChatGroq(
                api_key=key,
                model=model_name,
                temperature=0.3,
            )
        )

    return clients


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_groq_llm(model: str = None):
    clients = create_groq_clients(model=model)

    if not clients:
        raise ValueError("Pas de client Groq disponible")

    return clients[0]