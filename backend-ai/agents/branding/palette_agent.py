import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree

from agents.base_agent import BaseAgent, PipelineState
from config.branding_config import (
    LLM_CONFIG,
    PALETTE_TARGET_COUNT,
)
from llm.llm_factory import create_azure_openai_client
from prompts.branding.palette_prompt import (
    PALETTE_SYSTEM_PROMPT,
    build_palette_user_prompt,
)
from shared.branding.validators import validate_minimal_palettes

logger = logging.getLogger("brandai.palette_agent")


def _first_brand_name_from_options(brand_identity: dict) -> str:
    opts = (brand_identity or {}).get("name_options") or []
    for o in opts:
        if isinstance(o, dict):
            nm = str(o.get("name") or "").strip()
            if nm:
                return nm
    return ""


class PaletteAgent(BaseAgent):
    """Palettes en appel LLM direct + validation minimale locale."""

    def __init__(self):
        super().__init__(
            agent_name="palette_agent",
            temperature=LLM_CONFIG["temperature"],
            llm_model=LLM_CONFIG["model"],
            llm_max_tokens=LLM_CONFIG.get("max_tokens") or 4000,
        )
        self._provider = LLM_CONFIG.get("provider", "groq")

    async def _generate_raw_palettes(self, idea: dict, brand_name: str) -> str:
        system_prompt = PALETTE_SYSTEM_PROMPT
        user_prompt = build_palette_user_prompt(
            idea,
            brand_name,
            target=PALETTE_TARGET_COUNT,
        )
        if self._provider != "azure":
            return await self._call_llm(system_prompt, user_prompt)

        llm = create_azure_openai_client(
            temperature=self.temperature,
            max_tokens=self.llm_max_tokens,
        )
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = await llm.ainvoke(messages)
        content = response.content if response and getattr(response, "content", None) else ""
        return content if isinstance(content, str) else str(content)

    @traceable(name="palette_agent.run", tags=["branding", "palette_agent"])
    async def run(self, state: PipelineState) -> PipelineState:
        self._log_start(state)

        if not hasattr(state, "brand_identity") or state.brand_identity is None:
            state.brand_identity = {}

        brand_name = str(getattr(state, "brand_name_chosen", "") or "").strip()
        if not brand_name:
            brand_name = _first_brand_name_from_options(state.brand_identity)

        if not brand_name:
            msg = "Un nom de marque (choisi ou issu des propositions) est requis pour les palettes"
            state.brand_identity["palette_error"] = msg
            state.brand_identity["branding_status"] = "palette_failed"
            state.status = "palette_failed"
            state.errors.append(f"palette_agent: {msg}")
            self._log_error(msg)
            return state

        idea = state.clarified_idea or {}

        rt = get_current_run_tree()
        if rt:
            rt.metadata.update({
                "provider": self._provider,
                "model": LLM_CONFIG["model"],
                "sector": idea.get("sector", ""),
                "idea_name": idea.get("idea_name", ""),
                "target_palettes": PALETTE_TARGET_COUNT,
                "generation_mode": "single_llm_call_with_minimal_validation",
            })

        try:
            raw = await self._generate_raw_palettes(idea, brand_name)
            options = validate_minimal_palettes(raw, target=PALETTE_TARGET_COUNT)
        except Exception as e:
            msg = f"Échec génération palettes : {e}"
            self._log_error(msg)
            state.errors.append(f"palette_agent: {msg}")
            state.brand_identity["palette_error"] = msg
            state.brand_identity["branding_status"] = "palette_failed"
            state.status = "palette_failed"
            return state

        state.brand_identity["palette_options"] = options
        first = options[0]
        state.brand_identity["color_palette"] = {
            "palette_name": first.get("palette_name", ""),
            "palette_description": first.get("palette_description", ""),
            "swatches": first.get("swatches", []),
        }
        state.brand_identity.pop("palette_error", None)
        state.brand_identity["branding_status"] = "palette_generated"
        state.status = "palette_generated"
        self._log_success()
        logger.info(
            "[palette_agent] idea_id=%s brand=%s palettes=%s",
            state.idea_id,
            brand_name,
            len(options),
        )
        return state
