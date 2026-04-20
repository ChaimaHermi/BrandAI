import json
import os
import re
from typing import Any

import httpx

REFUSAL_MESSAGES = {
    "fraud": "BrandAI ne peut pas vous accompagner dans ce projet. Il semble viser à tromper des personnes.",
    "illegal": "BrandAI ne peut pas vous accompagner dans ce projet. Il implique des activités illégales.",
    "harmful": "BrandAI ne peut pas vous accompagner dans ce projet. Il pourrait causer du tort.",
    "default": "BrandAI ne peut pas vous accompagner dans ce type de projet.",
}

_NVIDIA_OPENAI_BASE = "https://integrate.api.nvidia.com/v1/chat/completions"
_DEFAULT_SAFETY_MODEL = os.getenv("NVIDIA_SAFETY_MODEL", "meta/llama-guard-4-12b")


def _nvidia_keys() -> list[str]:
    keys = [
        os.getenv("NVIDIA_API_KEY_1", "").strip(),
        os.getenv("NVIDIA_API_KEY_2", "").strip(),
        os.getenv("NVIDIA_API_KEY_3", "").strip(),
        os.getenv("NVIDIA_API_KEY_4", "").strip(),
    ]
    return [k for k in keys if k]


def _flatten_payload(payload: dict[str, Any]) -> str:
    try:
        return json.dumps(payload, ensure_ascii=False)
    except Exception:
        return str(payload)


def _extract_text_from_response(raw_text: str) -> str:
    txt = (raw_text or "").strip()
    if not txt:
        return ""
    try:
        parsed = json.loads(txt)
        if isinstance(parsed, dict):
            for key in ("output", "result", "text", "response"):
                if key in parsed and isinstance(parsed[key], str):
                    return parsed[key].strip()
    except Exception:
        pass
    return txt


def _to_internal_category(model_output: str) -> str:
    text = (model_output or "").lower()
    fraud_patterns = [
        "fraud", "scam", "phishing", "social engineering", "impersonation", "deception",
    ]
    illegal_patterns = [
        "weapon", "drugs", "illegal", "cyber abuse", "malware", "hacking", "forgery",
    ]
    harmful_patterns = [
        "violence", "self-harm", "suicide", "sexual", "minor", "hate", "dangerous",
    ]

    if any(p in text for p in fraud_patterns):
        return "fraud"
    if any(p in text for p in illegal_patterns):
        return "illegal"
    if any(p in text for p in harmful_patterns):
        return "harmful"
    return "harmful"


def _is_unsafe(model_output: str) -> bool:
    text = (model_output or "").strip().lower()
    if not text:
        return False
    if re.search(r"\bunsafe\b", text):
        return True
    if re.search(r"\bsafe\b", text):
        return False
    # Conservative fallback when model did not follow expected format.
    return False


async def check_safety_with_llama_guard(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Safety gate using NVIDIA-hosted Llama Guard.

    Returns:
      {
        "safe": bool,
        "reason_category": str | None,  # fraud | illegal | harmful
        "raw_output": str,
        "provider": "nvidia",
        "model": str,
      }
    """
    keys = _nvidia_keys()
    if not keys:
        raise RuntimeError("Aucune clé NVIDIA_API_KEY_* disponible pour safety check.")

    content = _flatten_payload(payload)
    system_prompt = (
        "You are a strict safety classifier. "
        "Classify the user content as SAFE or UNSAFE. "
        "If UNSAFE, provide brief violated categories."
    )

    body = {
        "model": _DEFAULT_SAFETY_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        "temperature": 0,
        "max_tokens": 256,
    }

    last_error: Exception | None = None
    for api_key in keys:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(45.0)) as client:
                response = await client.post(
                    _NVIDIA_OPENAI_BASE,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
                response.raise_for_status()
                message = response.json()["choices"][0]["message"]
                raw = (message.get("content") or message.get("reasoning_content") or "").strip()
                parsed = _extract_text_from_response(raw)
                unsafe = _is_unsafe(parsed)
                if not unsafe:
                    return {
                        "safe": True,
                        "reason_category": None,
                        "raw_output": parsed,
                        "provider": "nvidia",
                        "model": _DEFAULT_SAFETY_MODEL,
                    }
                return {
                    "safe": False,
                    "reason_category": _to_internal_category(parsed),
                    "raw_output": parsed,
                    "provider": "nvidia",
                    "model": _DEFAULT_SAFETY_MODEL,
                }
        except Exception as exc:  # pragma: no cover
            last_error = exc
            continue

    raise RuntimeError(f"Echec Llama-Guard safety check: {last_error}")


def get_refusal_message(category: str) -> str:
    """
    Fallback uniquement — utilisé si le LLM échoue.
    En temps normal, c'est le LLM qui génère le message.
    """
    return REFUSAL_MESSAGES.get(category, REFUSAL_MESSAGES["default"])