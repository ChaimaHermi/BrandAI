# ══════════════════════════════════════════════════════════════
# config/branding_config.py
# ══════════════════════════════════════════════════════════════

LLM_CONFIG = {
    "model": "openai/gpt-oss-120b",
    "temperature": 0.3,   # ↓ plus stable pour JSON
    "max_tokens": 8000,   # ↑ réduit les truncations
}

# Extensions à tester pour la disponibilité (Brandfetch).
# Note: Brandfetch ne garantit pas la disponibilité WHOIS, c'est un signal "likely".
# Suffixes de domaine à tester.
# Supporte les TLDs simples ("com") ET les ccSLDs ("co.za", "co.uk", ...).
DOMAIN_SUFFIXES = [
    "com",
    "io",
    "tn",
    "net",
    "org",
    "co",
    "app",
    "ai",
    "me",
    "dev",
    "xyz",
    "finance",
    # Common country second-level domains
    "co.uk",
    "co.za",
    "com.au",
    "co.in",
    "co.ma",
    "com.tn",
]

# Variantes à tester pour détecter des marques déjà existantes
# ex: studyfitnotes.com, getstudyfit.com, studyfitapp.com ...
DOMAIN_VARIANTS = [
    "{label}",
    "get{label}",
    "{label}app",
    "{label}hq",
    "{label}notes",
]

# LIMITS = {
#     "max_name_options": 5,
#     "min_name_options": 3,
# }