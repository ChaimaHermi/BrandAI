"""
Helpers LangSmith pour le Website Builder.

- Tags cohérents pour filtrer dans LangSmith (projet brand-ai).
- process_inputs / process_outputs pour éviter d'envoyer des prompts/HTML de 100k
  caractères et masquer les JWT.
"""

from __future__ import annotations

from typing import Any

TAGS_WEBSITE = ["website_builder"]
TAGS_TOOL = ["website_builder", "tool"]
TAGS_LLM = ["website_builder", "llm"]
TAGS_STREAM = ["website_builder", "stream", "sse"]
TAGS_CONTEXT = ["website_builder", "context"]
TAGS_QA = ["website_builder", "qa"]
TAGS_ORCH = ["website_builder", "orchestrator"]

_MAX_PROMPT_CHARS = 12_000
_MAX_HTML_HEAD = 2_000
_MAX_INSTRUCTION = 4_000


def _truncate(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s
    return s[:max_len] + f"\n... [truncated, {len(s)} chars total]"


def ctx_summary(ctx: Any) -> dict[str, Any] | None:
    if ctx is None:
        return None
    return {
        "idea_id": getattr(ctx, "idea_id", None),
        "brand_name": getattr(ctx, "brand_name", None),
        "language": getattr(ctx, "language", None),
    }


def strip_self(inputs: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in inputs.items() if k != "self"}


def redact_callables_and_token(inputs: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in inputs.items():
        if k == "self":
            continue
        if k in ("token", "access_token"):
            out[k] = "<redacted>"
        elif k == "emitter":
            out[k] = "<StepEmitter>"
        elif callable(v):
            out[k] = f"<callable {getattr(v, '__name__', type(v).__name__)}>"
        else:
            out[k] = v
    return out


def process_llm_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    out = strip_self(inputs)
    for key in ("system_prompt", "user_prompt"):
        if key in out and isinstance(out[key], str):
            out[key] = _truncate(out[key], _MAX_PROMPT_CHARS)
    return out


def process_llm_outputs(output: Any) -> Any:
    if isinstance(output, str):
        return _truncate(output, _MAX_PROMPT_CHARS)
    return output


def process_architecture_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    out = redact_callables_and_token(inputs)
    if "ctx" in out:
        out["ctx"] = ctx_summary(out["ctx"])
    return out


def process_architecture_outputs(output: Any) -> Any:
    if isinstance(output, dict):
        sections = output.get("sections")
        return {
            "sections_count": len(sections) if isinstance(sections, list) else 0,
            "animations_count": len(output.get("animations") or [])
            if isinstance(output.get("animations"), list)
            else 0,
            "language": output.get("language"),
            "keys": list(output.keys()),
        }
    return output


def process_content_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    out = redact_callables_and_token(inputs)
    if "ctx" in out:
        out["ctx"] = ctx_summary(out["ctx"])
    arch = out.get("architecture")
    if isinstance(arch, dict):
        secs = arch.get("sections")
        out["architecture"] = {
            "sections_count": len(secs) if isinstance(secs, list) else 0,
            "keys": list(arch.keys())[:24],
        }
    return out


def process_content_outputs(output: Any) -> Any:
    if isinstance(output, dict):
        sec = output.get("sections")
        n = len(sec) if isinstance(sec, dict) else 0
        return {"sections_keys_count": n, "top_keys": list(output.keys())}
    return output


def process_coder_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    out = redact_callables_and_token(inputs)
    if "ctx" in out:
        out["ctx"] = ctx_summary(out["ctx"])
    for key in ("architecture", "content"):
        blob = out.get(key)
        if isinstance(blob, dict):
            out[key] = {
                "keys": list(blob.keys())[:20],
                "size_estimate_chars": len(str(blob)),
            }
    return out


def process_coder_outputs(output: Any) -> Any:
    if isinstance(output, str):
        return {
            "html_chars": len(output),
            "html_head": _truncate(output, _MAX_HTML_HEAD),
        }
    return output


def process_revision_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    out = redact_callables_and_token(inputs)
    if "ctx" in out:
        out["ctx"] = ctx_summary(out["ctx"])
    h = out.pop("current_html", None)
    if isinstance(h, str):
        out["current_html_chars"] = len(h)
        out["current_html_preview"] = _truncate(h, _MAX_HTML_HEAD)
    instr = out.get("instruction")
    if isinstance(instr, str):
        out["instruction"] = _truncate(instr, _MAX_INSTRUCTION)
    return out


def process_revision_outputs(output: Any) -> Any:
    if isinstance(output, str):
        return {
            "html_chars": len(output),
            "html_head": _truncate(output, _MAX_HTML_HEAD),
        }
    return output


def process_refine_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    out = redact_callables_and_token(inputs)
    if "ctx" in out:
        out["ctx"] = ctx_summary(out["ctx"])
    desc = out.get("current_description")
    if isinstance(desc, dict):
        out["current_description"] = {
            "keys": list(desc.keys()),
            "sections_len": len(desc.get("sections") or [])
            if isinstance(desc.get("sections"), (list, dict))
            else 0,
        }
    fb = out.get("user_feedback")
    if isinstance(fb, str):
        out["user_feedback"] = _truncate(fb, _MAX_INSTRUCTION)
    return out


def process_refine_outputs(output: Any) -> Any:
    if isinstance(output, dict):
        return {
            "keys": list(output.keys()),
            "sections_len": len(output.get("sections") or [])
            if isinstance(output.get("sections"), (list, dict))
            else 0,
        }
    return output


def process_context_fetch_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    out = strip_self(inputs)
    if "access_token" in out:
        out["access_token"] = "<redacted>"
    return out


def process_context_fetch_outputs(output: Any) -> Any:
    if output is None:
        return None
    return ctx_summary(output)


def process_merge_description_outputs(output: Any) -> Any:
    if isinstance(output, dict):
        return {
            "keys": list(output.keys()),
            "sections_len": len(output.get("sections") or [])
            if isinstance(output.get("sections"), list)
            else 0,
            "animations_len": len(output.get("animations") or [])
            if isinstance(output.get("animations"), list)
            else 0,
        }
    return output


def process_ensure_html_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    out = strip_self(inputs)
    if "ctx" in out:
        out["ctx"] = ctx_summary(out["ctx"])
    html = out.pop("html", None)
    if isinstance(html, str):
        out["html_chars"] = len(html)
        out["html_preview"] = _truncate(html, _MAX_HTML_HEAD)
    return out


def process_ensure_html_outputs(output: Any) -> Any:
    if isinstance(output, tuple) and len(output) == 2:
        html, stats = output[0], output[1]
        if isinstance(html, str) and isinstance(stats, dict):
            return {
                "html_chars": len(html),
                "html_head": _truncate(html, _MAX_HTML_HEAD),
                "stats": stats,
            }
    return output


def process_generate_full_description_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    out = strip_self(inputs)
    if "ctx" in out:
        out["ctx"] = ctx_summary(out["ctx"])
    return out


def process_stream_description_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    return redact_callables_and_token(inputs)


def process_stream_refine_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    out = redact_callables_and_token(inputs)
    desc = out.get("current_description")
    if isinstance(desc, dict):
        out["current_description"] = {
            "keys": list(desc.keys()),
            "sections_len": len(desc.get("sections") or [])
            if isinstance(desc.get("sections"), (list, dict))
            else 0,
        }
    fb = out.get("user_feedback")
    if isinstance(fb, str):
        out["user_feedback"] = _truncate(fb, _MAX_INSTRUCTION)
    return out


def process_stream_generate_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    out = redact_callables_and_token(inputs)
    d = out.get("description")
    if isinstance(d, dict):
        out["description"] = {
            "keys": list(d.keys()),
            "sections_len": len(d.get("sections") or [])
            if isinstance(d.get("sections"), (list, dict))
            else 0,
        }
    elif d is None:
        out["description"] = None
    return out


def process_stream_revise_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    out = redact_callables_and_token(inputs)
    h = out.pop("current_html", None)
    if isinstance(h, str):
        out["current_html_chars"] = len(h)
        out["current_html_preview"] = _truncate(h, _MAX_HTML_HEAD)
    instr = out.get("instruction")
    if isinstance(instr, str):
        out["instruction"] = _truncate(instr, _MAX_INSTRUCTION)
    return out


def process_stream_result_outputs(output: Any) -> Any:
    """Les flux SSE ne retournent rien (None) — éviter logs inutiles."""
    return output


def process_route_inputs_idea_token(inputs: dict[str, Any]) -> dict[str, Any]:
    out = strip_self(inputs)
    if "token" in out:
        out["token"] = "<redacted>"
    return out


def process_save_html_route_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    out = strip_self(inputs)
    if "token" in out:
        out["token"] = "<redacted>"
    h = out.pop("html", None)
    if isinstance(h, str):
        out["html_chars"] = len(h)
        out["html_preview"] = _truncate(h, _MAX_HTML_HEAD)
    return out


def process_context_dict_outputs(output: Any) -> Any:
    if not isinstance(output, dict):
        return output
    summary = output.get("summary_md")
    out = {
        "idea_id": output.get("idea_id"),
        "brand_name": output.get("brand_name"),
        "language": output.get("language"),
        "keys": list(output.keys())[:40],
    }
    if isinstance(summary, str):
        out["summary_md_preview"] = _truncate(summary, 3000)
    return out


def process_save_html_outputs(output: Any) -> Any:
    if isinstance(output, dict):
        html = output.get("html")
        if isinstance(html, str):
            return {
                "idea_id": output.get("idea_id"),
                "html_chars": len(html),
                "html_stats": output.get("html_stats"),
            }
    return output
