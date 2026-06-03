# ══════════════════════════════════════════════════════════════
# Social Optimizer — config LLM (recommandations stratégiques)
# ══════════════════════════════════════════════════════════════

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from config.llm_defaults import DEFAULT_AZURE_DEPLOYMENT

SOCIAL_OPTIMIZER_AZURE_DEPLOYMENT = (
    (os.getenv("SOCIAL_OPTIMIZER_AZURE_DEPLOYMENT") or DEFAULT_AZURE_DEPLOYMENT).strip()
)

SOCIAL_OPTIMIZER_LLM_TEMPERATURE = 0.35

def _int_env(name: str, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


SOCIAL_OPTIMIZER_LLM_MAX_TOKENS = _int_env("SOCIAL_OPTIMIZER_LLM_MAX_TOKENS", 1600)
