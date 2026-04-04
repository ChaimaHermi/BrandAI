import os
from dotenv import load_dotenv
from pathlib import Path

# ─────────────────────────────────────────────
# LOAD .ENV FROM ROOT PROJECT
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)

# ─────────────────────────────────────────────
# UTILS
# ─────────────────────────────────────────────
def clean(keys):
    return [k.strip() for k in keys if k and k.strip()]

# ─────────────────────────────────────────────
# KEYS
# ─────────────────────────────────────────────
OPENROUTER_KEYS = clean([
    os.getenv("OPENROUTER_API_KEY"),
    os.getenv("OPENROUTER_API_KEY_1"),
    os.getenv("OPENROUTER_API_KEY_2"),
    os.getenv("OPENROUTER_API_KEY_3"),
])

GEMINI_KEYS = clean([
    os.getenv("GEMINI_API_KEY"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
])

GROQ_KEYS = clean([
    os.getenv("GROQ_API_KEY"),
    os.getenv("GROQ_API_KEY_2"),
    os.getenv("GROQ_API_KEY_3"),
])

# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────
if not (OPENROUTER_KEYS or GEMINI_KEYS or GROQ_KEYS):
    raise ValueError("Aucune API key trouvée dans .env")

# ─────────────────────────────────────────────
# AZURE OPENAI
# ─────────────────────────────────────────────
AZURE_OPENAI_ENDPOINT   = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_KEY        = os.getenv("AZURE_OPENAI_KEY", "")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
# Déploiement optionnel pour l’agent logo (ex. gpt-4.1). Si vide → même que AZURE_OPENAI_DEPLOYMENT.
AZURE_OPENAI_LOGO_DEPLOYMENT = (os.getenv("AZURE_OPENAI_LOGO_DEPLOYMENT") or "").strip()
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

# ─────────────────────────────────────────────
# LANGSMITH
# ─────────────────────────────────────────────
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")

if LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"]  = "true"
    os.environ["LANGCHAIN_ENDPOINT"]    = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"]     = LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"]     = "brand-ai"
    print("[settings] LangSmith -> enabled")
else:
    print("[settings] LangSmith -> disabled (no key)")

# ─────────────────────────────────────────────
# DEBUG
# ─────────────────────────────────────────────
print(
    f"[settings] Loaded .env from: {ENV_PATH}\n"
    f"[settings] Keys -> OpenRouter={len(OPENROUTER_KEYS)} | "
    f"Gemini={len(GEMINI_KEYS)} | Groq={len(GROQ_KEYS)}"
)