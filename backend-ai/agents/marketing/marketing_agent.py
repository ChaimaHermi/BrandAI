import logging
import json
from typing import Any, Dict

from agents.base_agent import BaseAgent, PipelineState
from config.marketing_config import MARKETING_LLM_CONFIG
from prompts.marketing.prompt_marketing_plan import PROMPT_MARKETING_PLAN

logger = logging.getLogger("brandai.marketing_agent")


class MarketingAgent(BaseAgent):
    def __init__(self):
        cfg = MARKETING_LLM_CONFIG
        super().__init__(
            agent_name="marketing_agent",
            temperature=float(cfg.get("temperature", 0.2)),
            llm_model=str(cfg.get("model", "openai/gpt-oss-120b")),
            llm_max_tokens=int(cfg.get("max_tokens", 3500)),
        )

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

        idea_output = {
            "short_pitch": idea.get("short_pitch"),
            "problem": idea.get("problem"),
            "solution_description": idea.get("solution_description"),
            "target_users": idea.get("target_users"),
            "sector": idea.get("sector"),
            "country": idea.get("country"),
            "country_code": idea.get("country_code"),
            "language": idea.get("language"),
            "budget_min": idea.get("budget_min"),
            "budget_max": idea.get("budget_max"),
            "budget_currency": idea.get("budget_currency"),
        }

        payload = {
            "idea_output": idea_output,
            "strategy_output": strategy,
            "budget_output": {
                "budget_min": idea.get("budget_min"),
                "budget_max": idea.get("budget_max"),
                "budget_currency": idea.get("budget_currency"),
            },
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
            if self._is_invalid_result(result):
                logger.warning("[marketing_agent] invalid result schema — retrying once with generation prompt")
                repaired_response = await self._call_llm(
                    system_prompt=(
                        PROMPT_MARKETING_PLAN
                        + "\n\nRÈGLE FINALE CRITIQUE: Retourne UNIQUEMENT un objet JSON valide "
                          "respectant STRICTEMENT le schéma demandé. Aucun texte hors JSON."
                    ),
                    user_prompt=context,
                )
                result = self._parse_response(repaired_response)

            if self._is_invalid_result(result):
                logger.warning("[marketing_agent] generation retry failed — attempting JSON repair pass")
                result = await self._repair_json_from_raw(response)

            if self._is_invalid_result(result):
                logger.error("[marketing_agent] invalid result after retry")
                return {"error": "invalid_json_or_schema"}

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

    async def _repair_json_from_raw(self, raw_response: str) -> Dict[str, Any]:
        """
        Try to convert malformed/raw model output into strict JSON schema.
        This pass does not invent additional business content: it only normalizes structure.
        """
        repair_system_prompt = (
            "You are a strict JSON repair engine.\n"
            "Task: Convert the provided text into ONE valid JSON object.\n"
            "Rules:\n"
            "- Output ONLY JSON, no markdown, no comments.\n"
            "- Keep original meaning/content; do not add new business claims.\n"
            "- If a field is missing, use empty string/empty array/object according to schema.\n"
            "- Ensure these top-level keys exist exactly:\n"
            '  "positioning", "messaging", "channels", "content_strategy", "go_to_market", "action_plan".\n'
        )

        repair_user_prompt = (
            "Repair this output into valid JSON:\n\n"
            f"{(raw_response or '')[:12000]}"
        )

        try:
            fixed = await self._call_llm(
                system_prompt=repair_system_prompt,
                user_prompt=repair_user_prompt,
            )
            return self._parse_response(fixed)
        except Exception as e:
            logger.warning(f"[marketing_agent] json repair failed: {e}")
            return {"error": "invalid_json_or_schema"}

    def _is_invalid_result(self, result: Dict[str, Any]) -> bool:
        if not isinstance(result, dict):
            return True
        if result.get("error"):
            return True
        required_top_level = [
            "positioning",
            "messaging",
            "channels",
            "content_strategy",
            "go_to_market",
            "action_plan",
        ]
        return not all(k in result for k in required_top_level)