# ══════════════════════════════════════════════════════════════
#  llm/llm_factory.py
#  Factory simple et propre
#  → Azure OpenAI (GPT-4 texte par défaut) + Groq (fallback) + NVIDIA (images / GLM)
# ══════════════════════════════════════════════════════════════

import os

from langchain_groq import ChatGroq
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from config.llm_defaults import DEFAULT_AZURE_DEPLOYMENT
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

    model_name = model if model else DEFAULT_AZURE_DEPLOYMENT

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
# REACT ORCHESTRATOR — Azure GPT-4 par défaut ; legacy NVIDIA si clés présentes
# ─────────────────────────────────────────────
_NVIDIA_OPENAI_BASE_URL = "https://integrate.api.nvidia.com/v1"


def create_react_orchestrator_llm(
    *,
    model: str | None = None,
    temperature: float = 0.35,
    max_tokens: int = 4096,
    azure_deployment: str | None = None,
):
    """LLM pour `create_react_agent` : Azure OpenAI (GPT-4) par défaut."""
    deployment = (azure_deployment or model or DEFAULT_AZURE_DEPLOYMENT).strip()
    if AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT:
        return create_azure_openai_client(
            temperature=temperature,
            max_tokens=max_tokens,
            azure_deployment=deployment,
        )

    nvidia_keys = [
        k.strip()
        for k in (
            os.getenv("NVIDIA_API_KEY_1", ""),
            os.getenv("NVIDIA_API_KEY_2", ""),
            os.getenv("NVIDIA_API_KEY_3", ""),
            os.getenv("NVIDIA_API_KEY_4", ""),
        )
        if k.strip()
    ]
    for api_key in nvidia_keys:
        return ChatOpenAI(
            base_url=_NVIDIA_OPENAI_BASE_URL,
            api_key=api_key,
            model=model or "openai/gpt-oss-120b",
            temperature=temperature,
            max_tokens=max_tokens,
        )

    raise RuntimeError(
        "Orchestrateur ReAct : configurez AZURE_OPENAI_* ou NVIDIA_API_KEY_1…4 dans .env."
    )


# ─────────────────────────────────────────────
# AZURE OPENAI CLIENT
# ─────────────────────────────────────────────
def create_azure_openai_client(
    temperature: float = 0.3,
    max_tokens: int = 1200,
    *,
    azure_deployment: str | None = None,
    max_retries: int = 2,
) -> AzureChatOpenAI:
    if not AZURE_OPENAI_KEY or not AZURE_OPENAI_ENDPOINT:
        raise RuntimeError(
            "Azure OpenAI non configuré. "
            "Vérifier AZURE_OPENAI_KEY et AZURE_OPENAI_ENDPOINT dans .env"
        )
    deployment = ((azure_deployment or "").strip() or AZURE_OPENAI_DEPLOYMENT)
    return AzureChatOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
        azure_deployment=deployment,
        api_version=AZURE_OPENAI_API_VERSION,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=max_retries,
    )


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_groq_llm(model: str = None):
    clients = create_groq_clients(model=model)

    if not clients:
        raise ValueError("Pas de client Groq disponible")

    return clients[0]