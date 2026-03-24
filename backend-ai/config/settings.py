import os
from dotenv import load_dotenv
from pathlib import Path

# ─────────────────────────────────────────────
# LOAD .ENV FROM ROOT PROJECT
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]  # remonte à "Brand AI"
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
# DEBUG
# ─────────────────────────────────────────────
print(
    f"[settings] Loaded .env from: {ENV_PATH}\n"
    f"[settings] Keys → OpenRouter={len(OPENROUTER_KEYS)} | "
    f"Gemini={len(GEMINI_KEYS)} | Groq={len(GROQ_KEYS)}"
)