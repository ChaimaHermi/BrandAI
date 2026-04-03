# ══════════════════════════════════════════════════════════════
#  llm/llm_factory.py
#  Factory simple et propre
#  → Groq uniquement (GPT OSS + LLaMA possible)
# ══════════════════════════════════════════════════════════════

from langchain_groq import ChatGroq
from langchain_openai import AzureChatOpenAI

from config.settings import (
    GROQ_KEYS,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION,
)


# ─────────────────────────────────────────────
# GROQ CLIENTS (DYNAMIQUE)
# ─────────────────────────────────────────────
def create_groq_clients(model: str = None, max_tokens: int | None = None) -> list:
    """
    Crée des clients Groq.
    - Par défaut → LLaMA
    - Sinon → modèle passé (ex: GPT OSS)
    - max_tokens → limite de sortie (requis pour gros JSON type market_analysis)
    """
    clients = []

    # 🔥 modèle par défaut
    model_name = model if model else "openai/gpt-oss-120b"

    for key in GROQ_KEYS:
        kwargs = {
            "api_key": key,
            "model": model_name,
            "temperature": 0.3,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        clients.append(ChatGroq(**kwargs))

    return clients


# ─────────────────────────────────────────────
# AZURE OPENAI CLIENT
# ─────────────────────────────────────────────
def create_azure_openai_client(
    temperature: float = 0.3,
    max_tokens: int = 1200,
) -> AzureChatOpenAI:
    if not AZURE_OPENAI_KEY or not AZURE_OPENAI_ENDPOINT:
        raise RuntimeError(
            "Azure OpenAI non configuré. "
            "Vérifier AZURE_OPENAI_KEY et AZURE_OPENAI_ENDPOINT dans .env"
        )
    return AzureChatOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
        azure_deployment=AZURE_OPENAI_DEPLOYMENT,
        api_version=AZURE_OPENAI_API_VERSION,
        temperature=temperature,
        max_tokens=max_tokens,
    )


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_groq_llm(model: str = None):
    clients = create_groq_clients(model=model)

    if not clients:
        raise ValueError("Pas de client Groq disponible")

    return clients[0]