"""
Helpers LangSmith partagés — tracing uniforme pour tous les agents BrandAI.

Activez via LANGCHAIN_API_KEY (ou LANGSMITH_API_KEY) dans Brand AI/.env
(voir config/settings.py).
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable, Sequence
from typing import Any, TypeVar

from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree

F = TypeVar("F", bound=Callable[..., Any])

_MAX_PROMPT_CHARS = 12_000
_MAX_OUTPUT_CHARS = 8_000


def _truncate(text: str, max_len: int = _MAX_PROMPT_CHARS) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"\n... [truncated, {len(text)} chars total]"


def enrich_run_metadata(**fields: Any) -> None:
    """Ajoute des métadonnées au run LangSmith courant (si tracing actif)."""
    rt = get_current_run_tree()
    if rt is not None:
        clean = {k: v for k, v in fields.items() if v is not None}
        if clean:
            rt.metadata.update(clean)


def pipeline_state_metadata(state: Any) -> dict[str, Any]:
    """Résumé léger d'un PipelineState pour les traces."""
    if state is None:
        return {}
    idea = getattr(state, "clarified_idea", None) or {}
    if not isinstance(idea, dict):
        idea = {}
    return {
        "idea_id": getattr(state, "idea_id", None),
        "sector": idea.get("sector") or getattr(state, "sector", None),
        "country_code": idea.get("country_code"),
        "language": idea.get("language"),
        "status": getattr(state, "status", None),
    }


def process_llm_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    out = dict(inputs)
    agent = out.pop("agent", None)
    if agent is not None:
        out["agent_name"] = getattr(agent, "agent_name", None)
        out["llm_model"] = getattr(agent, "llm_model", None)
    for key in ("system_prompt", "user_prompt"):
        if key in out and isinstance(out[key], str):
            out[key] = _truncate(out[key])
    return out


def process_llm_outputs(output: Any) -> Any:
    if isinstance(output, str):
        return _truncate(output, _MAX_OUTPUT_CHARS)
    return output


def process_agent_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in inputs.items():
        if k == "self":
            agent = v
            out["agent_name"] = getattr(agent, "agent_name", None)
            continue
        if k == "state" and hasattr(v, "idea_id"):
            out["pipeline"] = pipeline_state_metadata(v)
            continue
        if k in ("access_token", "token") and v:
            out[k] = "<redacted>"
            continue
        if isinstance(v, str) and len(v) > 2000:
            out[k] = _truncate(v, 2000)
        elif isinstance(v, dict) and len(str(v)) > 4000:
            out[k] = {"keys": list(v.keys())[:30], "size_chars": len(str(v))}
        else:
            out[k] = v
    return out


def process_agent_outputs(output: Any) -> Any:
    if isinstance(output, dict):
        return {"keys": list(output.keys())[:40], "size_chars": len(str(output))}
    if hasattr(output, "idea_id"):
        return {
            "idea_id": getattr(output, "idea_id", None),
            "status": getattr(output, "status", None),
        }
    if isinstance(output, str) and len(output) > _MAX_OUTPUT_CHARS:
        return _truncate(output, _MAX_OUTPUT_CHARS)
    return output


def process_tool_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    out = dict(inputs)
    q = out.get("query")
    if isinstance(q, str):
        out["query"] = _truncate(q, 500)
    url = out.get("url")
    if isinstance(url, str) and len(url) > 300:
        out["url"] = url[:300] + "..."
    return out


def process_tool_outputs(output: Any) -> Any:
    if isinstance(output, list):
        return {"result_count": len(output), "type": "list"}
    if isinstance(output, dict):
        return {"keys": list(output.keys())[:20], "size_chars": len(str(output))}
    return output


async def traced_llm_dispatch(agent: Any, system_prompt: str, user_prompt: str) -> str:
    """Point d'entrée LLM tracé (appelé depuis BaseAgent._call_llm)."""
    enrich_run_metadata(
        agent_name=getattr(agent, "agent_name", None),
        llm_model=getattr(agent, "llm_model", None),
        temperature=getattr(agent, "temperature", None),
    )
    from agents.base_agent import NVIDIA_MODELS
    from config.settings import AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY

    if agent.llm_model in NVIDIA_MODELS:
        return await agent._call_nvidia_direct(system_prompt, user_prompt)
    if AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT:
        return await agent._call_azure_direct(system_prompt, user_prompt)
    return await agent._call_langchain(system_prompt, user_prompt)


# Enveloppe traceable (définie après la fonction pour éviter import circulaire au load)
traced_llm_dispatch = traceable(
    name="brandai.llm_call",
    run_type="llm",
    tags=["brandai", "llm"],
    process_inputs=process_llm_inputs,
    process_outputs=process_llm_outputs,
)(traced_llm_dispatch)


def _agent_trace_preamble(*args: Any) -> None:
    self_obj = args[0] if args else None
    if self_obj is not None and hasattr(self_obj, "agent_name"):
        enrich_run_metadata(agent_name=self_obj.agent_name)
    for arg in args:
        if hasattr(arg, "idea_id") and hasattr(arg, "clarified_idea"):
            enrich_run_metadata(**pipeline_state_metadata(arg))
            break


def agent_trace(
    name: str,
    *,
    tags: Sequence[str] | None = None,
    run_type: str = "chain",
) -> Callable[[F], F]:
    """Décorateur pour entrées d'agents (async ou sync)."""
    tag_list = ["brandai", "agent", *(tags or [])]

    def decorator(fn: F) -> F:
        if inspect.iscoroutinefunction(fn):

            @traceable(
                name=name,
                run_type=run_type,
                tags=tag_list,
                process_inputs=process_agent_inputs,
                process_outputs=process_agent_outputs,
            )
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                _agent_trace_preamble(*args)
                return await fn(*args, **kwargs)

            return async_wrapper  # type: ignore[return-value]

        @traceable(
            name=name,
            run_type=run_type,
            tags=tag_list,
            process_inputs=process_agent_inputs,
            process_outputs=process_agent_outputs,
        )
        @functools.wraps(fn)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            _agent_trace_preamble(*args)
            return fn(*args, **kwargs)

        return sync_wrapper  # type: ignore[return-value]

    return decorator


def graph_node_trace(node_name: str) -> Callable[[F], F]:
    """Décorateur pour les nœuds LangGraph (market, marketing, …)."""
    return agent_trace(
        f"market_graph.{node_name}",
        tags=["market_analysis", "langgraph", node_name],
    )


def trace_sync_tool(name: str, *, tags: Sequence[str] | None = None) -> Callable[[F], F]:
    """Décorateur pour outils synchrones (Tavily, SerpAPI, …)."""
    tag_list = ["brandai", "tool", *(tags or [])]

    def decorator(fn: F) -> F:
        @traceable(
            name=name,
            run_type="tool",
            tags=tag_list,
            process_inputs=process_tool_inputs,
            process_outputs=process_tool_outputs,
        )
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
