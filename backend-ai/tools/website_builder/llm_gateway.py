from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from langsmith import traceable
from langchain_core.messages import HumanMessage, SystemMessage

from agents.base_agent import BaseAgent
from agents.base_agent import PipelineState
from config.website_builder_config import (
    DESCRIPTION_MAX_TOKENS,
    DESCRIPTION_TEMPERATURE,
    WEBSITE_BUILDER_AZURE_DEPLOYMENT,
    WEBSITE_LLM_MAX_RETRIES,
)
from llm.llm_factory import create_azure_openai_client

logger = logging.getLogger("brandai.website_builder.llm_gateway")


class WebsiteBuilderLlmGateway(BaseAgent):
    """Technical LLM gateway used by the website builder orchestrator."""

    def __init__(self) -> None:
        super().__init__(
            agent_name="website_builder_llm_gateway",
            temperature=DESCRIPTION_TEMPERATURE,
            llm_max_tokens=DESCRIPTION_MAX_TOKENS,
            llm_model=f"azure/{WEBSITE_BUILDER_AZURE_DEPLOYMENT}",
        )

    async def run(self, state: PipelineState) -> Any:
        raise NotImplementedError("WebsiteBuilderLlmGateway n'expose pas run(); utilise invoke_llm().")

    @traceable(name="website_builder.llm.invoke", tags=["website_builder", "llm", "azure"])
    async def invoke_llm(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> str:
        return await self._invoke_azure(system_prompt, user_prompt, **kwargs)

    def parse_json_output(self, raw: str) -> dict[str, Any]:
        return self._parse_json(raw)

    async def _invoke_azure(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float,
        max_tokens: int,
        phase: str = "unknown",
        timeout_seconds: float = 90.0,
    ) -> str:
        client = create_azure_openai_client(
            temperature=temperature,
            max_tokens=max_tokens,
            azure_deployment=WEBSITE_BUILDER_AZURE_DEPLOYMENT,
            max_retries=1,
        )
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = None
        timeout_exc: Exception | None = None
        for attempt in range(1 + max(0, WEBSITE_LLM_MAX_RETRIES)):
            started = time.monotonic()
            logger.info(
                "[website_builder] AZURE CALL START phase=%s attempt=%d/%d deployment=%s temp=%.2f max_tokens=%d prompt_chars=%d timeout=%s",
                phase,
                attempt + 1,
                1 + max(0, WEBSITE_LLM_MAX_RETRIES),
                WEBSITE_BUILDER_AZURE_DEPLOYMENT,
                temperature,
                max_tokens,
                len(system_prompt) + len(user_prompt),
                f"{timeout_seconds:.1f}s" if timeout_seconds and timeout_seconds > 0 else "disabled",
            )
            try:
                if timeout_seconds and timeout_seconds > 0:
                    response = await asyncio.wait_for(
                        client.ainvoke(messages),
                        timeout=timeout_seconds,
                    )
                else:
                    response = await client.ainvoke(messages)
                break
            except (TimeoutError, asyncio.TimeoutError) as exc:
                timeout_exc = exc
                elapsed = time.monotonic() - started
                logger.warning(
                    "[website_builder] AZURE CALL TIMEOUT phase=%s attempt=%d after %.2fs",
                    phase,
                    attempt + 1,
                    elapsed,
                )
                if attempt < WEBSITE_LLM_MAX_RETRIES:
                    await asyncio.sleep(1.2 * (attempt + 1))
                continue
            except Exception as exc:
                elapsed = time.monotonic() - started
                logger.error(
                    "[website_builder] AZURE CALL ERROR phase=%s attempt=%d after %.2fs error=%s: %s",
                    phase,
                    attempt + 1,
                    elapsed,
                    type(exc).__name__,
                    str(exc)[:300],
                )
                if attempt < WEBSITE_LLM_MAX_RETRIES:
                    await asyncio.sleep(1.2 * (attempt + 1))
                    continue
                raise RuntimeError(
                    f"Azure OpenAI erreur non-recuperable phase={phase}: {exc}"
                ) from exc

        if response is None:
            if timeout_exc is not None:
                raise RuntimeError(
                    f"Azure OpenAI timeout pendant la phase {phase} "
                    f"(>{timeout_seconds:.0f}s, retries={WEBSITE_LLM_MAX_RETRIES})."
                ) from timeout_exc
            raise RuntimeError(
                f"Azure OpenAI n'a retourne aucune reponse exploitable (phase={phase})."
            )

        content = (response.content or "").strip()
        if not content:
            raise RuntimeError("Azure OpenAI a renvoye une reponse vide.")
        return content

