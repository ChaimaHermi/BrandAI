import logging

from agents.base_agent import BaseAgent, PipelineState
from agents.branding.name_agent import NameAgent
from agents.branding.palette_agent import PaletteAgent, _first_brand_name_from_options

logger = logging.getLogger("brandai.branding_orchestrator")


class BrandingOrchestratorAgent(BaseAgent):
    """Orchestrates branding sub-agents: naming puis palettes (slogan / logo en flux dédiés)."""

    def __init__(self):
        super().__init__("branding_orchestrator")
        self.name_agent = NameAgent()
        self.palette_agent = PaletteAgent()

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

            resolved = str(getattr(state, "brand_name_chosen", "") or "").strip()
            if not resolved:
                resolved = _first_brand_name_from_options(state.brand_identity or {})
            if resolved:
                state.brand_name_chosen = resolved
                prefs = getattr(state, "palette_preferences", None) or {}
                state.palette_preferences = prefs if isinstance(prefs, dict) else {}
                try:
                    state = await self.palette_agent.run(state)
                except Exception as e:
                    msg = str(e)
                    state.errors.append(f"branding_orchestrator:palette_agent:{msg}")
                    state.brand_identity.setdefault("agent_errors", {})["palette"] = msg
                    state.brand_identity["branding_status"] = "partial"
                    state.status = "branding_done"
                    state.brand_identity["completed_agents"] = sorted(completed)
                    state.brand_identity["pending_agents"] = ["palette", "slogan", "logo"]
                    logger.exception("[branding_orchestrator] palette_agent exception: %s", msg)
                    return state

                if state.status == "palette_generated":
                    completed.add("palette")
                    state.brand_identity["branding_status"] = "palette_generated"
                    state.brand_identity["pending_agents"] = ["slogan", "logo"]
                else:
                    err = state.brand_identity.get("palette_error") or "palette_failed"
                    state.brand_identity.setdefault("agent_errors", {})["palette"] = err
                    state.brand_identity["branding_status"] = "partial"
                    state.brand_identity["pending_agents"] = ["palette", "slogan", "logo"]
            else:
                state.brand_identity["branding_status"] = "partial"
                state.brand_identity["pending_agents"] = ["palette", "slogan", "logo"]
                logger.warning("[branding_orchestrator] no brand name resolved, skip palette")

            state.brand_identity["completed_agents"] = sorted(completed)
            state.status = "branding_done"
            logger.info(
                "[branding_orchestrator] branding_done completed_agents=%s status_meta=%s",
                state.brand_identity.get("completed_agents"),
                state.brand_identity.get("branding_status"),
            )
            return state

        msg = state.brand_identity.get("name_error") or "name_agent failed"
        state.brand_identity["agent_errors"]["name"] = msg
        state.brand_identity["branding_status"] = "failed"
        state.status = "error"
        logger.error(f"[branding_orchestrator] name phase failed: {msg}")
        return state
