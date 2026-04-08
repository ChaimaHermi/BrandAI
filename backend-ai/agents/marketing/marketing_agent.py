import logging
import json
from typing import Any, Dict

from agents.base_agent import BaseAgent, PipelineState
from prompts.marketing.prompt_marketing_plan import PROMPT_MARKETING_PLAN

logger = logging.getLogger("brandai.marketing_agent")


class MarketingAgent(BaseAgent):
    def __init__(self):
        super().__init__("marketing_agent")

    def _top_n(self, items, n=3):
        if not isinstance(items, list):
            return []
        out = []
        for item in items:
            if item is None:
                continue
            if isinstance(item, str):
                item = item.strip()
                if not item:
                    continue
            out.append(item)
            if len(out) >= n:
                break
        return out

    def _build_marketing_context(self, idea: Dict[str, Any], market: Dict[str, Any]) -> str:
        strategy = (market or {}).get("strategy", {}) or {}
        voc = (market or {}).get("voc", {}) or {}

        payload = {
            "idea": {
                "short_pitch": idea.get("short_pitch"),
                "problem": idea.get("problem"),
                "solution_description": idea.get("solution_description"),
                "target_users": idea.get("target_users"),
                "sector": idea.get("sector"),
                "country": idea.get("country"),
                "country_code": idea.get("country_code"),
                "language": idea.get("language"),
            },
            "strategy_analysis": strategy,
        }

        # Fallback léger: si strategy est vide, garder quelques signaux VOC.
        if not strategy:
            pains = self._top_n((voc.get("pain_points") or []), n=3)
            frus = self._top_n((voc.get("frustrations") or []), n=3)
            payload["fallback_voc_signals"] = {
                "pain_points_top3": pains,
                "frustrations_top3": frus,
            }

        return json.dumps(payload, ensure_ascii=False, indent=2)

    async def run(self, state: PipelineState) -> Dict[str, Any]:
        logger.info(f"[marketing_agent] ▶ START | idea_id={state.idea_id}")

        idea = state.clarified_idea or {}
        market = state.market_analysis or {}

        if not idea or not market:
            logger.error("[marketing_agent] missing inputs")
            return {"error": "missing inputs"}

        context = self._build_marketing_context(idea, market)

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