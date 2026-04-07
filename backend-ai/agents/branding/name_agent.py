import json
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.prebuilt import create_react_agent
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree

from agents.base_agent import BaseAgent, PipelineState
from config.branding_config import (
    LLM_CONFIG,
    NAME_AGENT_RECURSION_LIMIT,
    NAME_AGENT_VERBOSE_REACT,
    NAME_TARGET_COUNT,
)
from llm.llm_factory import create_azure_openai_client
from prompts.branding.name_prompt import (
    NAME_REACT_SYSTEM_PROMPT,
    attach_naming_preferences,
    build_name_react_user_message,
)
from tools.branding.name_tools import (
    make_generate_names_tool,
    make_validate_names_tool,
)


class NameAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            agent_name="name_agent",
            temperature=LLM_CONFIG["temperature"],
            llm_model=LLM_CONFIG["model"],
            llm_max_tokens=LLM_CONFIG["max_tokens"],
        )
        self._provider = LLM_CONFIG.get("provider", "groq")

    # ─────────────────────────────────────────
    # EXTRACT Brandfetch results from ReAct trace
    # ─────────────────────────────────────────
    @staticmethod
    def _extract_available_from_tool_messages(messages: list, *, limit: int) -> list:
        """Collects name dicts with availability not_exists from validate_names tool outputs."""
        seen: set[str] = set()
        out: list = []
        for msg in messages or []:
            if not isinstance(msg, ToolMessage):
                continue
            tool_name = getattr(msg, "name", None) or ""
            if tool_name and tool_name != "validate_names":
                continue
            raw = msg.content
            if not isinstance(raw, str) or not raw.strip():
                continue
            try:
                data = json.loads(raw)
            except Exception:
                continue
            if isinstance(data, dict) and data.get("error"):
                continue
            if not isinstance(data, list):
                continue
            for item in data:
                if not isinstance(item, dict):
                    continue
                if item.get("availability") != "not_exists":
                    continue
                nm = str(item.get("name") or "").strip()
                if not nm:
                    continue
                key = nm.lower()
                if key in seen:
                    continue
                seen.add(key)
                out.append({
                    "name": nm,
                    "description": str(item.get("description") or "").strip(),
                    "availability": "not_exists",
                    "matched_name": item.get("matched_name"),
                })
                if len(out) >= limit:
                    return out
        return out

    # ─────────────────────────────────────────
    # HELPERS D'AFFICHAGE TERMINAL
    # ─────────────────────────────────────────
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
        if tool_name == "validate_names":
            try:
                data = json.loads(raw)
                if isinstance(data, list):
                    parts = []
                    for x in data[:12]:
                        if not isinstance(x, dict):
                            continue
                        nm = str(x.get("name") or "?").strip()
                        av = str(x.get("availability") or "?")
                        parts.append(f"{nm} -> {av}")
                    extra = f" (+{len(data) - 12} autres)" if len(data) > 12 else ""
                    return "; ".join(parts) + extra
            except Exception:
                pass
        if tool_name == "generate_names":
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    opts = data.get("name_options", [])
                    names = [
                        str(o.get("name") or "").strip()
                        for o in opts
                        if isinstance(o, dict)
                    ]
                    names = [n for n in names if n][:12]
                    return "proposes: " + ", ".join(names) + (
                        f" (+{len(opts) - len(names)} autres)" if len(opts) > len(names) else ""
                    )
            except Exception:
                pass
        return cls._truncate(raw, 520)

    @classmethod
    def _log_react_message(cls, msg, step: int) -> None:
        """Affiche un message du graphe au style ReAct (terminal)."""
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
        cls._print(f"\n--- [{type(msg).__name__}] (etape {step}) ---\n{cls._truncate(str(msg.content), 400)}")

    async def _invoke_react_with_optional_trace(
        self,
        agent,
        user_content: str,
        recursion_limit: int,
    ) -> dict:
        """ainvoke, ou astream + logs terminal si NAME_AGENT_VERBOSE_REACT."""
        cfg = {"recursion_limit": recursion_limit}
        initial = {"messages": [HumanMessage(content=user_content)]}

        if not NAME_AGENT_VERBOSE_REACT:
            return await agent.ainvoke(initial, config=cfg)

        self._print("\n>>> ReAct trace (stream_mode=values) — chaque pas = nouveau message\n")
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

    # ─────────────────────────────────────────
    # LangGraph ReAct (tool-calling loop)
    # ─────────────────────────────────────────
    @traceable(name="name_agent.react_invoke", tags=["branding", "name_agent", "react"])
    async def _run_react_name_agent(
        self,
        llm,
        idea_context: dict,
        *,
        idea_id: int | str | None = None,
        target: int = NAME_TARGET_COUNT,
        recursion_limit: int = NAME_AGENT_RECURSION_LIMIT,
    ) -> list:
        rt = get_current_run_tree()
        if rt:
            rt.metadata.update({
                "target": target,
                "recursion_limit": recursion_limit,
                "agent": "langgraph_react",
            })

        generate_tool = make_generate_names_tool(llm=llm, idea=idea_context, idea_id=idea_id)
        validate_tool = make_validate_names_tool(idea_id=idea_id)
        tools = [generate_tool, validate_tool]

        system_prompt = NAME_REACT_SYSTEM_PROMPT.format(target=target)
        agent = create_react_agent(
            llm,
            tools,
            prompt=system_prompt,
            name="name_react",
        )

        user_content = build_name_react_user_message(idea_context, target=target)

        self._header("LangGraph ReAct agent (name search)")
        self.logger.info(
            "[name_agent] ReAct graph | recursion_limit=%s verbose_terminal=%s",
            recursion_limit,
            NAME_AGENT_VERBOSE_REACT,
        )

        result = await self._invoke_react_with_optional_trace(
            agent,
            user_content,
            recursion_limit,
        )

        messages = result.get("messages") or []
        available = self._extract_available_from_tool_messages(messages, limit=target)

        self._print(f"\n[ReAct done] noms not_exists extraits: {len(available)}/{target}")
        for i, n in enumerate(available, 1):
            self._print(f"  {i}. {n.get('name')}")

        return available[:target]

    # ─────────────────────────────────────────
    # MAIN
    # ─────────────────────────────────────────
    @traceable(name="name_agent.run", tags=["branding", "name_agent"])
    async def run(self, state: PipelineState):

        self._log_start(state)

        try:
            if not hasattr(state, "brand_identity") or state.brand_identity is None:
                state.brand_identity = {}

            if not state.clarified_idea:
                raise ValueError("clarified_idea is required")

            idea = state.clarified_idea

            # ── Enrich the LangSmith run with idea metadata ──────────────────────
            rt = get_current_run_tree()
            if rt:
                rt.metadata.update({
                    "provider": self._provider,
                    "model": LLM_CONFIG["model"],
                    "sector": idea.get("sector", ""),
                    "country": idea.get("country", ""),
                    "language": idea.get("language", "fr"),
                    "idea_name": idea.get("idea_name", ""),
                    "name_target_count": NAME_TARGET_COUNT,
                })

            required_fields = [
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
                state.brand_identity["branding_status"] = "name_failed"
                state.status = "name_failed"
                self._log_error(f"missing_fields: {', '.join(missing)}")
                return state

            idea_context = {
                "idea_name": idea.get("idea_name") or state.name or "",
                "sector": idea.get("sector") or state.sector or "",
                "target_users": idea.get("target_users") or state.target_audience or "",
                "problem": idea.get("problem") or "",
                "solution_description": idea.get("solution_description") or "",
                "country": idea.get("country") or "",
                "country_code": idea.get("country_code") or "",
                "language": idea.get("language") or "fr",
            }
            prefs = getattr(state, "naming_preferences", None)
            if prefs:
                idea_context = attach_naming_preferences(idea_context, prefs)

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

            # ─────────────────────────────────────────
            # RETRY LOOP (gestion quota/rotation clés)
            # ─────────────────────────────────────────
            name_options = None
            last_error = None

            for attempt in range(self.max_retries):
                try:
                    if self._provider == "azure":
                        llm = create_azure_openai_client(
                            temperature=self.temperature,
                            max_tokens=LLM_CONFIG["max_tokens"],
                        )
                        model_info = f"azure:{LLM_CONFIG['model']}"
                    else:
                        llm = self.llm_rotator.get_client(self.temperature)
                        model_info = self.llm_rotator.current_info()

                    self.logger.info(
                        f"[name_agent] attempt {attempt + 1}/{self.max_retries} | {model_info}"
                    )

                    name_options = await self._run_react_name_agent(
                        llm,
                        idea_context,
                        idea_id=state.idea_id,
                        target=NAME_TARGET_COUNT,
                        recursion_limit=NAME_AGENT_RECURSION_LIMIT,
                    )
                    break

                except Exception as e:
                    last_error = e
                    if self._provider == "groq":
                        if _is_tpd_error(e):
                            self.logger.error(f"[name_agent] TPD quota exhausted | {str(e)[:200]}")
                            raise RuntimeError(
                                "Quota journalier Groq (TPD) épuisé. "
                                "Réessaie dans quelques heures ou change de modèle."
                            ) from e
                        if _is_quota_error(e):
                            rotated = self.llm_rotator.rotate()
                            self.logger.warning(
                                f"[name_agent] quota error attempt {attempt + 1} | "
                                f"rotated={rotated} | {str(e)[:180]}"
                            )
                            if rotated:
                                continue
                    raise

            if name_options is None:
                err_detail = str(last_error) if last_error else "aucune tentative effectuée"
                raise RuntimeError(f"name search failed after {self.max_retries} retries: {err_detail}")

            # ─────────────────────────────────────────
            # RÉSULTAT
            # ─────────────────────────────────────────
            if not name_options:
                state.brand_identity["name_options"] = []
                state.brand_identity["name_error"] = (
                    f"Impossible de trouver {NAME_TARGET_COUNT} noms disponibles "
                    "après toutes les tentatives."
                )
                state.brand_identity["branding_status"] = "name_failed"
                state.status = "name_failed"
                return state

            for n in name_options:
                n["top_choice"] = True

            state.brand_identity["name_options"] = name_options
            state.brand_identity.pop("name_error", None)
            state.brand_identity["branding_status"] = "name_generated"
            state.status = "name_generated"

            self._log_success()
            return state

        except Exception as e:
            self._log_error(e)
            state.errors.append(f"name_agent: {str(e)}")
            state.status = "error"
            if state.brand_identity is not None:
                state.brand_identity.setdefault("agent_errors", {})
                state.brand_identity["agent_errors"]["name"] = str(e)
                state.brand_identity["branding_status"] = "failed"
            return state
