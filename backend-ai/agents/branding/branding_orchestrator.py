import logging

from agents.base_agent import BaseAgent, PipelineState
from agents.branding.name_agent import NameAgent

logger = logging.getLogger("brandai.branding_orchestrator")


class BrandingOrchestratorAgent(BaseAgent):
    """Orchestrates branding sub-agents.

    Current phase: only NameAgent is wired.
    Future phases can plug slogan/palette/logo while keeping output schema stable.
    """

    def __init__(self):
        super().__init__("branding_orchestrator")
        self.name_agent = NameAgent()

    @staticmethod
    def _init_brand_identity(state: PipelineState) -> None:
        if not hasattr(state, "brand_identity") or state.brand_identity is None:
            state.brand_identity = {}

        state.brand_identity.setdefault("name_options", [])
        state.brand_identity.setdefault("slogan_options", [])
        state.brand_identity.setdefault("logo_concepts", [])
        state.brand_identity.setdefault("color_palette", {})
        state.brand_identity.setdefault("completed_agents", [])
        state.brand_identity.setdefault("pending_agents", ["slogan", "logo", "palette"])
        state.brand_identity.setdefault("agent_errors", {})
        state.brand_identity.setdefault("branding_status", "running")

    async def run(self, state: PipelineState) -> PipelineState:
        logger.info(f"[branding_orchestrator] START idea_id={state.idea_id}")
        self._init_brand_identity(state)

        if not state.clarified_idea:
            msg = "clarified_idea is required before branding orchestration"
            state.errors.append(f"branding_orchestrator: {msg}")
            state.brand_identity["agent_errors"]["branding_orchestrator"] = msg
            state.brand_identity["branding_status"] = "failed"
            state.status = "error"
            logger.error(f"[branding_orchestrator] {msg}")
            return state

        try:
            state = await self.name_agent.run(state)
        except Exception as e:
            msg = str(e)
            state.errors.append(f"branding_orchestrator:name_agent:{msg}")
            state.brand_identity["agent_errors"]["name"] = msg
            state.brand_identity["branding_status"] = "failed"
            state.status = "error"
            logger.error(f"[branding_orchestrator] name_agent exception: {msg}")
            return state

        if state.status == "name_generated":
            completed = set(state.brand_identity.get("completed_agents", []))
            completed.add("name")
            state.brand_identity["completed_agents"] = sorted(completed)
            state.brand_identity["pending_agents"] = ["slogan", "logo", "palette"]
            state.brand_identity["branding_status"] = "partial"
            state.status = "branding_done"
            logger.info("[branding_orchestrator] SUCCESS name phase completed")
            return state

        msg = state.brand_identity.get("name_error") or "name_agent failed"
        state.brand_identity["agent_errors"]["name"] = msg
        state.brand_identity["branding_status"] = "failed"
        state.status = "error"
        logger.error(f"[branding_orchestrator] name phase failed: {msg}")
        return state
