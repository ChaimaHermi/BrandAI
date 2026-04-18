"""
Trace terminal du graphe ReAct (style Thought / Action / Observation).

Inspiré de `name_agent._invoke_react_with_optional_trace` — activé si
`CONTENT_AGENT_VERBOSE_TERMINAL=1` dans `content_generation_config`.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

logger = logging.getLogger("brandai.content_react_trace")


def _truncate(s: str, max_len: int = 700) -> str:
    t = (s or "").strip()
    if len(t) <= max_len:
        return t
    return t[:max_len] + f"... [tronqué, {len(t)} car. au total]"


def _print(msg: str = "") -> None:
    print(msg, flush=True)


def _summarize_tool_observation(tool_name: str, raw: str, max_len: int = 900) -> str:
    s = (raw or "").strip()
    if len(s) <= max_len:
        return s
    return s[:max_len] + f"... [tronqué, {len(s)} car.]"


def log_react_message(msg: Any, step: int) -> None:
    """Affiche un message du graphe LangGraph au format ReAct lisible."""
    if isinstance(msg, HumanMessage):
        _print(f"\n--- [Message utilisateur] ---\n{_truncate(str(msg.content), 600)}")
        return
    if isinstance(msg, SystemMessage):
        _print(f"\n--- [System] (étape {step}) ---\n{_truncate(str(msg.content), 400)}")
        return
    if isinstance(msg, AIMessage):
        tcalls = getattr(msg, "tool_calls", None) or []
        text = (msg.content or "").strip() if isinstance(msg.content, str) else ""
        if text:
            _print(f"\n--- [Thought] (étape {step}) ---\n{_truncate(text, 700)}")
        if tcalls:
            _print(f"\n--- [Action] (étape {step}) ---")
            for tc in tcalls:
                if isinstance(tc, dict):
                    name = tc.get("name", "?")
                    args = tc.get("args", {})
                else:
                    name = getattr(tc, "name", "?")
                    args = getattr(tc, "args", {})
                try:
                    arg_s = (
                        json.dumps(args, ensure_ascii=False, indent=2)
                        if isinstance(args, dict)
                        else str(args)
                    )
                except Exception:
                    arg_s = str(args)
                _print(f"  -> {name}({_truncate(arg_s, 400)})")
        if not text and not tcalls:
            _print(f"\n--- [AIMessage vide] (étape {step}) ---")
        return
    if isinstance(msg, ToolMessage):
        tname = getattr(msg, "name", None) or "tool"
        raw = msg.content if isinstance(msg.content, str) else str(msg.content)
        _print(f"\n--- [Observation] (étape {step}) tool={tname} ---")
        _print(_summarize_tool_observation(tname, raw))
        return
    _print(f"\n--- [{type(msg).__name__}] (étape {step}) ---\n{_truncate(str(getattr(msg, 'content', msg)), 400)}")


async def invoke_react_with_optional_terminal_trace(
    agent: Any,
    *,
    initial: dict[str, Any],
    recursion_limit: int,
    verbose: bool,
) -> dict[str, Any]:
    """
    `ainvoke` classique, ou `astream` + logs si verbose.
    Retourne l'état final du graphe (dict avec clé `messages`).
    """
    cfg: dict[str, Any] = {"recursion_limit": recursion_limit}

    if not verbose:
        return await agent.ainvoke(initial, config=cfg)

    _print("\n" + "=" * 60)
    _print("  Content generation — ReAct (trace terminal)")
    _print("=" * 60 + "\n")

    final_state: dict | None = None
    prev_len = 0
    step = 0

    async for state in agent.astream(initial, config=cfg, stream_mode="values"):
        final_state = state
        msgs = state.get("messages") or []
        for i in range(prev_len, len(msgs)):
            step += 1
            log_react_message(msgs[i], step)
        prev_len = len(msgs)

    if final_state is None:
        logger.warning("[react_trace] astream vide → fallback ainvoke")
        return await agent.ainvoke(initial, config=cfg)

    _print("\n" + "-" * 60)
    _print(f"  Fin de la trace — {step} message(s) affiché(s)")
    _print("-" * 60 + "\n")

    return final_state
