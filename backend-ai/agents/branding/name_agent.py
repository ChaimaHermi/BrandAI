from agents.base_agent import BaseAgent, PipelineState
from config.branding_config import LLM_CONFIG
from prompts.branding.name_prompt import build_name_user_prompt


class NameAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            agent_name="name_agent",
            temperature=LLM_CONFIG["temperature"],
            llm_model=LLM_CONFIG["model"],
            llm_max_tokens=LLM_CONFIG["max_tokens"],
        )

    # ─────────────────────────────────────────
    async def run(self, state: PipelineState):

        self._log_start(state)

        try:
            system_prompt = self._build_system_prompt()
            user_prompt   = build_name_user_prompt(state)

            raw = await self._call_llm(system_prompt, user_prompt)

            data = self._parse_json(raw)

            options = data.get("name_options", [])

            # stocker dans state
            state.brand_identity["name_options"] = options

            state.status = "name_generated"

            self._log_success()

            return state

        except Exception as e:
            self._log_error(e)
            state.errors.append(f"name_agent: {str(e)}")
            state.status = "error"
            return state

    # ─────────────────────────────────────────
    def _build_system_prompt(self) -> str:
        return """
You are a senior branding expert.

You generate high-quality startup brand names.

Rules:
- creative but realistic
- simple and memorable
- no long explanations
- return ONLY valid JSON
"""