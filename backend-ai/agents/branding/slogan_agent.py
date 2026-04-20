import json
import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.prebuilt import create_react_agent
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree

from agents.base_agent import BaseAgent, PipelineState
from config.branding_config import (
    LLM_CONFIG,
    SLOGAN_AGENT_RECURSION_LIMIT,
    SLOGAN_AGENT_VERBOSE_REACT,
    SLOGAN_TARGET_COUNT,
)
from llm.llm_factory import create_azure_openai_client
from prompts.branding.slogan_prompt import (
    SLOGAN_REACT_SYSTEM_PROMPT,
    build_slogan_react_user_message,
)
from tools.branding.slogan_tools import make_draft_slogans_tool, make_validate_slogans_tool

logger = logging.getLogger("brandai.slogan_agent")


class SloganAgent(BaseAgent):
    """Slogans via LangGraph ReAct (draft + validation outils maison)."""

    def __init__(self):
        self._slogan_max_tokens = min(LLM_CONFIG.get("max_tokens") or 1200, 1600)
        super().__init__(
            agent_name="slogan_agent",
            temperature=LLM_CONFIG["temperature"],
            llm_model=LLM_CONFIG["model"],
            llm_max_tokens=self._slogan_max_tokens,
        )
        self._provider = LLM_CONFIG.get("provider", "groq")

    @staticmethod
    def _extract_validated_slogan_options(messages: list) -> list[dict[str, Any]] | None:
        for msg in reversed(messages or []):
            if not isinstance(msg, ToolMessage):
                continue
            tool_name = getattr(msg, "name", None) or ""
            if tool_name != "validate_slogans":
                continue
            raw = msg.content
            if not isinstance(raw, str) or not raw.strip():
                continue
            try:
                data = json.loads(raw)
            except Exception:
                continue
            if not isinstance(data, dict) or not data.get("ok"):
                continue
            opts = data.get("slogan_options")
            if isinstance(opts, list) and len(opts) >= SLOGAN_TARGET_COUNT:
                return opts[:SLOGAN_TARGET_COUNT]
        return None

    @staticmethod
    def _print(msg: str = "") -> None:
        print(msg, flush=True)

    @staticmethod
    def _header(title: str) -> None:
        bar = "=" * 56
        print(f"\n{bar}", flush=True)
        print(f"  {title}", flush=True)
        print(bar, flush=True)

    @staticmethod
    def _truncate(s: str, max_len: int = 480) -> str:
        s = (s or "").strip()
        if len(s) <= max_len:
            return s
        return s[: max_len - 3] + "..."

    @classmethod
    def _summarize_tool_observation(cls, tool_name: str, raw: str) -> str:
        if not raw or not isinstance(raw, str):
            return str(raw)[:400]
        if tool_name == "validate_slogans":
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    if data.get("ok"):
                        opts = data.get("slogan_options") or []
                        return f"ok=true, {len(opts)} slogan(s)"
                    return f"ok=false: {cls._truncate(str(data.get('error') or raw), 400)}"
            except Exception:
                pass
        if tool_name == "draft_slogans":
            return cls._truncate(raw, 520)
        return cls._truncate(raw, 520)

    @classmethod
    def _log_react_message(cls, msg, step: int) -> None:
        if isinstance(msg, HumanMessage):
            cls._print(f"\n--- [Message utilisateur] ---\n{cls._truncate(str(msg.content), 600)}")
            return
        if isinstance(msg, SystemMessage):
            cls._print(f"\n--- [System] (etape {step}) ---\n{cls._truncate(str(msg.content), 400)}")
            return
        if isinstance(msg, AIMessage):
            tcalls = getattr(msg, "tool_calls", None) or []
            text = (msg.content or "").strip() if isinstance(msg.content, str) else ""
            if text:
                cls._print(f"\n--- [Thought] (etape {step}) ---\n{cls._truncate(text, 700)}")
            if tcalls:
                cls._print(f"\n--- [Action] (etape {step}) ---")
                for tc in tcalls:
                    if isinstance(tc, dict):
                        name = tc.get("name", "?")
                        args = tc.get("args", {})
                    else:
                        name = getattr(tc, "name", "?")
                        args = getattr(tc, "args", {})
                    try:
                        arg_s = json.dumps(args, ensure_ascii=False, indent=2) if isinstance(args, dict) else str(args)
                    except Exception:
                        arg_s = str(args)
                    cls._print(f"  -> {name}({cls._truncate(arg_s, 400)})")
            if not text and not tcalls:
                cls._print(f"\n--- [AIMessage vide] (etape {step}) ---")
            return
        if isinstance(msg, ToolMessage):
            tname = getattr(msg, "name", None) or "tool"
            raw = msg.content if isinstance(msg.content, str) else str(msg.content)
            cls._print(f"\n--- [Observation] (etape {step}) tool={tname} ---")
            cls._print(cls._summarize_tool_observation(tname, raw))
            return
        cls._print(f"\n--- [{type(msg).__name__}] (etape {step}) ---\n{cls._truncate(str(getattr(msg, 'content', '')), 400)}")

    async def _invoke_react_with_optional_trace(
        self,
        agent,
        user_content: str,
        recursion_limit: int,
    ) -> dict:
        cfg = {"recursion_limit": recursion_limit}
        initial = {"messages": [HumanMessage(content=user_content)]}

        if not SLOGAN_AGENT_VERBOSE_REACT:
            return await agent.ainvoke(initial, config=cfg)

        self._print("\n>>> ReAct slogans (stream_mode=values)\n")
        final_state: dict | None = None
        prev_len = 0
        step = 0
        async for state in agent.astream(initial, config=cfg, stream_mode="values"):
            final_state = state
            msgs = state.get("messages") or []
            for i in range(prev_len, len(msgs)):
                step += 1
                self._log_react_message(msgs[i], step)
            prev_len = len(msgs)

        if final_state is None:
            return await agent.ainvoke(initial, config=cfg)
        return final_state

    @traceable(name="slogan_agent.react_invoke", tags=["branding", "slogan_agent", "react"])
    async def _run_react_slogan_agent(
        self,
        llm,
        idea: dict,
        brand_name: str,
        prefs: dict,
        *,
        recursion_limit: int = SLOGAN_AGENT_RECURSION_LIMIT,
    ) -> list[dict[str, Any]] | None:
        rt = get_current_run_tree()
        if rt:
            rt.metadata.update({
                "recursion_limit": recursion_limit,
                "agent": "langgraph_react_slogan",
                "target_slogans": SLOGAN_TARGET_COUNT,
            })

        draft_tool = make_draft_slogans_tool(
            llm,
            idea,
            brand_name,
            prefs,
            target=SLOGAN_TARGET_COUNT,
        )
        validate_tool = make_validate_slogans_tool(
            target=SLOGAN_TARGET_COUNT,
            preferences=prefs,
        )
        tools = [draft_tool, validate_tool]

        system_prompt = SLOGAN_REACT_SYSTEM_PROMPT.format(target=SLOGAN_TARGET_COUNT)
        agent = create_react_agent(
            llm,
            tools,
            prompt=system_prompt,
            name="slogan_react",
        )

        user_content = build_slogan_react_user_message(brand_name, target=SLOGAN_TARGET_COUNT)

        self._header("LangGraph ReAct — slogans")
        self.logger.info(
            "[slogan_agent] ReAct | recursion_limit=%s verbose=%s",
            recursion_limit,
            SLOGAN_AGENT_VERBOSE_REACT,
        )

        result = await self._invoke_react_with_optional_trace(
            agent,
            user_content,
            recursion_limit,
        )

        messages = result.get("messages") or []
        options = self._extract_validated_slogan_options(messages)
        if options:
            self._print(f"\n[ReAct slogans] validés: {len(options)} slogan(s)")
        return options

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

        def _is_tpd_error(err: Exception) -> bool:
            s = str(err).lower()
            return "tokens per day" in s or "tpd" in s

        def _is_quota_error(err: Exception) -> bool:
            s = str(err).lower()
            return any(k in s for k in [
                "429", "413", "rate_limit", "rate_limit_exceeded",
                "tokens per minute", "tokens per day",
                "request too large", "tpm", "tpd",
            ])

        options: list[dict[str, Any]] | None = None
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                if self._provider == "azure":
                    llm = create_azure_openai_client(
                        temperature=self.temperature,
                        max_tokens=self._slogan_max_tokens,
                    )
                else:
                    llm = self.llm_rotator.get_client(self.temperature)

                rt = get_current_run_tree()
                if rt:
                    rt.metadata.update({
                        "provider": self._provider,
                        "model": LLM_CONFIG["model"],
                        "sector": idea.get("sector", ""),
                        "idea_name": idea.get("idea_name", ""),
                    })

                self.logger.info(
                    "[slogan_agent] attempt %s/%s",
                    attempt + 1,
                    self.max_retries,
                )

                options = await self._run_react_slogan_agent(
                    llm,
                    idea,
                    brand_name,
                    prefs,
                    recursion_limit=SLOGAN_AGENT_RECURSION_LIMIT,
                )
                if options:
                    break
                last_error = RuntimeError(
                    "Validation des slogans non confirmée par l'outil validate_slogans (ok: true)."
                )
            except Exception as e:
                last_error = e
                if self._provider == "groq":
                    if _is_tpd_error(e):
                        self.logger.error("[slogan_agent] TPD quota | %s", str(e)[:200])
                        self._log_error(e)
                        msg = (
                            "Quota journalier Groq (TPD) épuisé. "
                            "Réessaie dans quelques heures ou change de modèle."
                        )
                        state.errors.append(f"slogan_agent: {msg}")
                        state.brand_identity["slogan_error"] = msg
                        state.brand_identity["branding_status"] = "slogan_failed"
                        state.status = "slogan_failed"
                        return state
                    if _is_quota_error(e):
                        rotated = self.llm_rotator.rotate()
                        self.logger.warning(
                            "[slogan_agent] quota | rotated=%s | %s",
                            rotated,
                            str(e)[:180],
                        )
                        if rotated:
                            continue
                self._log_error(e)
                msg = str(e)
                state.errors.append(f"slogan_agent: {msg}")
                state.brand_identity["slogan_error"] = msg
                state.brand_identity["branding_status"] = "slogan_failed"
                state.status = "slogan_failed"
                return state

        if not options:
            err_detail = str(last_error) if last_error else "aucun slogan validé"
            msg = f"Échec génération slogans : {err_detail}"
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
