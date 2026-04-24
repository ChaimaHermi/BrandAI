import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree

from agents.base_agent import BaseAgent, PipelineState
from config.branding_config import (
    LLM_CONFIG,
    SLOGAN_TARGET_COUNT,
)
from llm.llm_factory import create_azure_openai_client
from prompts.branding.slogan_prompt import (
    SLOGAN_SYSTEM_PROMPT,
    build_slogan_user_prompt,
)
from shared.branding.validators import validate_minimal_slogans

logger = logging.getLogger("brandai.slogan_agent")


class SloganAgent(BaseAgent):
    """Slogans en appel LLM direct + validation minimale locale."""

    def __init__(self):
        self._slogan_max_tokens = min(LLM_CONFIG.get("max_tokens") or 1200, 1600)
        super().__init__(
            agent_name="slogan_agent",
            temperature=LLM_CONFIG["temperature"],
            llm_model=LLM_CONFIG["model"],
            llm_max_tokens=self._slogan_max_tokens,
        )
        self._provider = LLM_CONFIG.get("provider", "groq")

    async def _generate_raw_slogans(self, idea: dict, brand_name: str, prefs: dict) -> str:
        system_prompt = SLOGAN_SYSTEM_PROMPT
        user_prompt = build_slogan_user_prompt(
            idea,
            brand_name,
            prefs,
            target=SLOGAN_TARGET_COUNT,
        )
        if self._provider != "azure":
            return await self._call_llm(system_prompt, user_prompt)

        llm = create_azure_openai_client(
            temperature=self.temperature,
            max_tokens=self._slogan_max_tokens,
        )
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = await llm.ainvoke(messages)
        content = response.content if response and getattr(response, "content", None) else ""
        return content if isinstance(content, str) else str(content)

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

        rt = get_current_run_tree()
        if rt:
            rt.metadata.update({
                "provider": self._provider,
                "model": LLM_CONFIG["model"],
                "sector": idea.get("sector", ""),
                "idea_name": idea.get("idea_name", ""),
                "target_slogans": SLOGAN_TARGET_COUNT,
                "generation_mode": "single_llm_call_with_minimal_validation",
            })

        try:
            raw = await self._generate_raw_slogans(idea, brand_name, prefs)
            options = validate_minimal_slogans(raw, target=SLOGAN_TARGET_COUNT)
        except Exception as e:
            msg = f"Échec génération slogans : {e}"
            self._log_error(msg)
            state.errors.append(f"slogan_agent: {msg}")
            state.brand_identity["slogan_error"] = msg
            state.brand_identity["branding_status"] = "slogan_failed"
            state.status = "slogan_failed"
            return state

        state.brand_identity["slogan_options"] = options
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
