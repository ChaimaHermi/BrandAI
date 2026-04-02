from agents.base_agent import BaseAgent, PipelineState
from config.branding_config import LLM_CONFIG
from prompts.branding.name_prompt import build_name_user_prompt
from tools.branding.name_tools import validate_name_list


class NameAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            agent_name="name_agent",
            temperature=LLM_CONFIG["temperature"],
            llm_model=LLM_CONFIG["model"],
            llm_max_tokens=LLM_CONFIG["max_tokens"],
        )

    # ─────────────────────────────────────────
    # MAIN
    # ─────────────────────────────────────────
    async def run(self, state: PipelineState):

        self._log_start(state)

        try:
            # Ensure container
            if not hasattr(state, "brand_identity") or state.brand_identity is None:
                state.brand_identity = {}

            # 🔒 STRICT: clarified_idea required
            if not state.clarified_idea:
                raise ValueError("clarified_idea is required")

            idea = state.clarified_idea

            required_fields = [
                "idea_name",
                "sector",
                "target_users",
                "problem",
                "solution_description",
                "country",
            ]

            missing = [k for k in required_fields if not str(idea.get(k) or "").strip()]

            if missing:
                state.brand_identity["name_options"] = []
                state.brand_identity["name_error"] = (
                    "Données clarifiées incomplètes: " + ", ".join(missing)
                )
                state.status = "name_failed"
                self._log_error(f"missing_fields: {', '.join(missing)}")
                return state

            # 1. Build prompts
            system_prompt = self._build_system_prompt()
            user_prompt = build_name_user_prompt(state)

            # 2. Call LLM
            raw = await self._call_llm(system_prompt, user_prompt)

            # 3. Parse JSON
            try:
                data = self._parse_json(raw)
                options = data.get("name_options", [])
            except Exception:
                options = []

            if not options:
                state.brand_identity["name_options"] = []
                state.brand_identity["name_error"] = (
                    "Impossible de générer des noms pour le moment."
                )
                state.status = "name_failed"
                self._log_error("invalid_llm_output")
                return state

            # 4. Validate
            validated = await validate_name_list(options)

            # 5. Save
            state.brand_identity["name_options"] = validated
            state.brand_identity.pop("name_error", None)

            state.status = "name_generated"

            self._log_success()

            return state

        except Exception as e:
            self._log_error(e)
            state.errors.append(f"name_agent: {str(e)}")
            state.status = "error"
            return state

    # ─────────────────────────────────────────
    # SYSTEM PROMPT
    # ─────────────────────────────────────────
    def _build_system_prompt(self) -> str:
        return """
You are a senior branding expert.

All outputs MUST be in French.

You generate high-quality startup brand names.

Rules:
- creative but realistic
- simple and memorable
- no long explanations
- return ONLY valid JSON
"""