import logging
from typing import Any, Dict

from agents.base_agent import BaseAgent, PipelineState
from prompts.marketing.prompt_marketing_plan import PROMPT_MARKETING_PLAN

logger = logging.getLogger("brandai.marketing_agent")


class MarketingAgent(BaseAgent):
    def __init__(self):
        super().__init__("marketing_agent")

    async def run(self, state: PipelineState) -> Dict[str, Any]:
        logger.info(f"[marketing_agent] ▶ START | idea_id={state.idea_id}")

        idea = state.clarified_idea or {}
        market = state.market_analysis or {}

        if not idea or not market:
            logger.error("[marketing_agent] missing inputs")
            return {"error": "missing inputs"}

        context = f"""
IDEA:
{idea}

MARKET ANALYSIS:
{market}
"""

        try:
            response = await self._call_llm(
                system_prompt=PROMPT_MARKETING_PLAN,
                user_prompt=context,
            )

            result = self._parse_response(response)
            state.market_analysis = state.market_analysis or {}
            state.market_analysis["marketing"] = result

            logger.info("[marketing_agent] ✅ SUCCESS")
            return result

        except Exception as e:
            logger.error(f"[marketing_agent] ❌ ERROR: {e}")
            return {"error": str(e)}

    # ─────────────────────────────────────────
    # PARSER
    # ─────────────────────────────────────────

    def _parse_response(self, response: str) -> Dict[str, Any]:
        try:
            return self._parse_json(response)
        except Exception:
            logger.warning("[marketing_agent] fallback parsing")
            return {
                "error": "invalid_json",
                "raw": response[:1000]
            }