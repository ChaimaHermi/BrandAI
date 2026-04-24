import os
from dotenv import load_dotenv
from pathlib import Path
import re

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

# Hugging Face (logo image : InferenceClient + Replicate) — HF_TOKEN_1 / HF_TOKEN_2 prioritaires
_seen_hf: set[str] = set()
HF_KEYS: list[str] = []
_hf_numbered: list[tuple[int, str]] = []
_hfa_numbered: list[tuple[int, str]] = []
for _name, _val in os.environ.items():
    _v = (_val or "").strip()
    if not _v:
        continue
    _m_hf = re.fullmatch(r"HF_TOKEN_(\d+)", _name)
    if _m_hf:
        _hf_numbered.append((int(_m_hf.group(1)), _v))
        continue
    _m_hfa = re.fullmatch(r"HUGGINGFACE_API_KEY_(\d+)", _name)
    if _m_hfa:
        _hfa_numbered.append((int(_m_hfa.group(1)), _v))

_hf_numbered.sort(key=lambda x: x[0])
_hfa_numbered.sort(key=lambda x: x[0])

for _k in (
    *(v for _, v in _hf_numbered),
    *(v for _, v in _hfa_numbered),
    os.getenv("HF_TOKEN"),
    os.getenv("HUGGINGFACE_HUB_TOKEN"),
    os.getenv("HUGGINGFACE_API_KEY"),
):
    if _k and _k.strip() and _k.strip() not in _seen_hf:
        _seen_hf.add(_k.strip())
        HF_KEYS.append(_k.strip())

# Pollinations (fallback image logo) — optionnel. Ex. POLLINATIONS_API_KEY=pk_… (sans espaces autour du =).
_pollinations_key = (os.getenv("POLLINATIONS_API_KEY") or "").strip()
if not _pollinations_key:
    _pollinations_key = (os.getenv("Pollination_API_Key") or "").strip()
if not _pollinations_key:
    _pollinations_key = (os.getenv("POLLINATION_API_KEY") or "").strip()
POLLINATIONS_API_KEY = _pollinations_key if _pollinations_key else None

# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────
if not (OPENROUTER_KEYS or GEMINI_KEYS or GROQ_KEYS or HF_KEYS):
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
    f"Gemini={len(GEMINI_KEYS)} | Groq={len(GROQ_KEYS)} | HF={len(HF_KEYS)}"
)