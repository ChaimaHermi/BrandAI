import asyncio
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable

from agents.base_agent import BaseAgent, PipelineState
from config.branding_config import LLM_CONFIG, SLOGAN_TARGET_COUNT
from llm.llm_factory import create_azure_openai_client
from prompts.branding.slogan_prompt import (
    SLOGAN_SYSTEM_PROMPT,
    build_slogan_user_prompt,
)

logger = logging.getLogger("brandai.slogan_agent")


def _normalize_slogan_options(raw: list) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if isinstance(item, str) and item.strip():
            out.append({"text": item.strip(), "rationale": ""})
            continue
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or item.get("slogan") or "").strip()
        if not text:
            continue
        rationale = str(item.get("rationale") or item.get("description") or "").strip()
        out.append({"text": text, "rationale": rationale})
    return out


class SloganAgent(BaseAgent):
    """Génère des slogans à partir du contexte clarifié, du nom choisi et des préférences one-shot."""

    def __init__(self):
        super().__init__(
            agent_name="slogan_agent",
            temperature=LLM_CONFIG["temperature"],
            llm_model=LLM_CONFIG["model"],
            llm_max_tokens=min(LLM_CONFIG.get("max_tokens") or 1200, 1600),
        )
        self._provider = LLM_CONFIG.get("provider", "groq")
        self._slogan_max_tokens = min(LLM_CONFIG.get("max_tokens") or 1200, 1600)

    async def _invoke_slogan_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Même routage que NameAgent : Azure → AzureChatOpenAI, sinon rotator Groq / _call_llm."""
        if self._provider == "azure":
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
            attempt = 0
            last_error = None
            while attempt < self.max_retries:
                try:
                    llm = create_azure_openai_client(
                        temperature=self.temperature,
                        max_tokens=self._slogan_max_tokens,
                    )
                    response = await llm.ainvoke(messages)
                    content = response.content if response else ""
                    if not (content or "").strip():
                        raise RuntimeError("Empty response from Azure")
                    return content
                except Exception as e:
                    last_error = e
                    attempt += 1
                    await asyncio.sleep(2 ** attempt)
            raise RuntimeError(f"Azure slogan LLM failed: {last_error}")

        return await self._call_llm(system_prompt, user_prompt)

    @traceable(name="slogan_agent.run", tags=["branding", "slogan_agent"])
    async def run(self, state: PipelineState) -> PipelineState:
        self._log_start(state)

        if not hasattr(state, "brand_identity") or state.brand_identity is None:
            state.brand_identity = {}

        brand_name = str(getattr(state, "brand_name_chosen", "") or "").strip()
        if not brand_name:
            msg = "brand_name_chosen est requis pour générer des slogans"
            state.brand_identity["slogan_error"] = msg
            state.brand_identity["branding_status"] = "slogan_failed"
            state.status = "slogan_failed"
            state.errors.append(f"slogan_agent: {msg}")
            self._log_error(msg)
            return state

        idea = state.clarified_idea or {}
        prefs = getattr(state, "slogan_preferences", None) or {}

        try:
            user_prompt = build_slogan_user_prompt(
                idea,
                brand_name,
                prefs,
                target=SLOGAN_TARGET_COUNT,
            )
            raw = await self._invoke_slogan_llm(SLOGAN_SYSTEM_PROMPT, user_prompt)
            data = self._parse_json(raw)
        except Exception as e:
            self._log_error(e)
            msg = str(e)
            state.errors.append(f"slogan_agent: {msg}")
            state.brand_identity["slogan_error"] = msg
            state.brand_identity["branding_status"] = "slogan_failed"
            state.status = "slogan_failed"
            return state

        options = _normalize_slogan_options(data.get("slogan_options") or [])
        if len(options) < 1:
            msg = "Aucun slogan exploitable dans la réponse du modèle"
            state.brand_identity["slogan_error"] = msg
            state.brand_identity["branding_status"] = "slogan_failed"
            state.status = "slogan_failed"
            self._log_error(msg)
            return state

        state.brand_identity["slogan_options"] = options[: SLOGAN_TARGET_COUNT]
        state.brand_identity["chosen_brand_name"] = brand_name
        state.brand_identity.pop("slogan_error", None)
        state.brand_identity["branding_status"] = "slogan_generated"
        state.status = "slogan_generated"
        self._log_success()
        logger.info(
            "[slogan_agent] idea_id=%s brand=%s count=%s",
            state.idea_id,
            brand_name,
            len(state.brand_identity["slogan_options"]),
        )
        return state
