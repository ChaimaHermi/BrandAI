# ══════════════════════════════════════════════════════════════
# LLM texte par défaut — Azure OpenAI (GPT-4.x)
# Remplace openai/gpt-oss-120b (NVIDIA NIM) pour tout le texte.
# Images : NVIDIA Flux (logo, content) — inchangé.
# ══════════════════════════════════════════════════════════════

import os

from config.settings import AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_LOGO_DEPLOYMENT

DEFAULT_AZURE_DEPLOYMENT = (
    (os.getenv("DEFAULT_LLM_DEPLOYMENT") or AZURE_OPENAI_DEPLOYMENT or "gpt-4.1").strip()
)

LOGO_AZURE_DEPLOYMENT = (AZURE_OPENAI_LOGO_DEPLOYMENT or DEFAULT_AZURE_DEPLOYMENT).strip()

DEFAULT_AZURE_MAX_TOKENS = 4096
