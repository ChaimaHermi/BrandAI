"""
LLM texte du module content generation — Azure OpenAI (GPT-4.1 / déploiement .env).
Les images restent sur NVIDIA Flux via content_image_client.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable

from agents.base_agent import BaseAgent, PipelineState
from config.content_generation_config import CONTENT_AZURE_DEPLOYMENT, CONTENT_LLM_CONFIG
from llm.llm_factory import create_azure_openai_client
from observability.langsmith_tracing import enrich_run_metadata

logger = logging.getLogger("brandai.content_azure_llm")


@traceable(name="brandai.content_azure_llm", run_type="llm", tags=["content_generation", "azure"])
async def call_content_azure_llm(
    *,
    agent_name: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    azure_deployment: str | None = None,
) -> str:
    deployment = (azure_deployment or CONTENT_AZURE_DEPLOYMENT).strip()
    enrich_run_metadata(
        agent_name=agent_name,
        llm_model=deployment,
        temperature=temperature,
        llm_provider="azure",
    )
    llm = create_azure_openai_client(
        temperature=temperature,
        max_tokens=max_tokens,
        azure_deployment=deployment,
        max_retries=2,
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    logger.info("[%s] Azure → %s | max_tokens=%d", agent_name, deployment, max_tokens)
    response = await llm.ainvoke(messages)
    content = response.content if response and getattr(response, "content", None) else ""
    text = content if isinstance(content, str) else str(content)
    text = (text or "").strip()
    if not text:
        raise RuntimeError(f"Réponse Azure vide ({deployment}).")
    logger.info("[%s] Azure OK | chars≈%d", agent_name, len(text))
    return text


@traceable(
    name="brandai.azure_llm_json",
    run_type="llm",
    tags=["azure", "json_object"],
)
async def call_azure_llm_json_object(
    *,
    agent_name: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    azure_deployment: str | None = None,
) -> dict:
    """Appel Azure avec response_format=json_object (social optimizer, etc.)."""
    deployment = (azure_deployment or CONTENT_AZURE_DEPLOYMENT).strip()
    enrich_run_metadata(
        agent_name=agent_name,
        llm_model=deployment,
        temperature=temperature,
        llm_provider="azure",
    )
    llm = create_azure_openai_client(
        temperature=temperature,
        max_tokens=max_tokens,
        azure_deployment=deployment,
        max_retries=2,
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    logger.info("[%s] Azure JSON → %s | max_tokens=%d", agent_name, deployment, max_tokens)
    response = await llm.bind(response_format={"type": "json_object"}).ainvoke(messages)
    content = response.content if response and getattr(response, "content", None) else ""
    text = (content if isinstance(content, str) else str(content)).strip()
    if not text:
        raise RuntimeError(f"Réponse Azure JSON vide ({deployment}).")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Réponse Azure JSON invalide ({deployment}).") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"Réponse Azure JSON attendue (objet), reçu {type(data).__name__}.")
    logger.info("[%s] Azure JSON OK | keys=%s", agent_name, ",".join(list(data.keys())[:8]))
    return data


class ContentTextLLMBase(BaseAgent):
    """BaseAgent dont _call_llm passe par Azure (pas NVIDIA / Groq)."""

    def __init__(
        self,
        agent_name: str,
        *,
        temperature: float,
        llm_max_tokens: int,
        max_retries: int = 3,
    ) -> None:
        self._azure_deployment = CONTENT_AZURE_DEPLOYMENT
        super().__init__(
            agent_name,
            temperature=temperature,
            max_retries=max_retries,
            llm_model=self._azure_deployment,
            llm_max_tokens=llm_max_tokens,
        )

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        return await call_content_azure_llm(
            agent_name=self.agent_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=self.temperature,
            max_tokens=self.llm_max_tokens,
            azure_deployment=self._azure_deployment,
        )

    async def run(self, state: PipelineState) -> dict[str, Any]:
        return {}
