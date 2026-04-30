from langchain_core.prompts import PromptTemplate

from config.branding_config import NAME_TARGET_COUNT


def _fmt_list(items) -> str:
    if not items:
        return "—"
    if isinstance(items, str) and items.strip():
        return items.strip()
    if isinstance(items, (list, tuple)):
        cleaned = [str(x).strip() for x in items if str(x).strip()]
        return ", ".join(cleaned) if cleaned else "—"
    return "—"


def _fmt_str(s) -> str:
    t = (s or "").strip()
    return t if t else "—"


def attach_naming_preferences(idea: dict, prefs: dict | None) -> dict:
    """
    Fusionne les préférences utilisateur (one-shot, non persistées) dans le dict
    lu par build_name_user_prompt. Ne modifie pas le dict original.
    """
    out = dict(idea or {})
    if not prefs:
        return out
    out["user_brand_values"] = list(prefs.get("brand_values") or [])
    out["user_personality"] = list(prefs.get("personality") or [])
    out["user_feelings"] = list(prefs.get("user_feelings") or [])
    out["naming_language"] = (prefs.get("name_language") or "").strip() or "—"
    out["naming_length"] = (prefs.get("name_length") or "").strip() or "—"
    out["naming_include"] = (prefs.get("include_keywords") or "").strip() or "—"
    out["naming_exclude"] = (prefs.get("exclude_keywords") or "").strip() or "—"
    out["user_remarks"] = (prefs.get("user_remarks") or "").strip()
    return out


# ─────────────────────────────────────────
# SEMANTIC ALIGNMENT dynamique par secteur
# ─────────────────────────────────────────
_SECTOR_THEMES: dict[str, list[str]] = {
    "fintech":     ["confiance financière", "sécurité", "croissance", "investissement", "flux"],
    "finance":     ["confiance financière", "sécurité", "croissance", "investissement", "flux"],
    "santé":       ["soin", "bien-être", "guérison", "vitalité", "équilibre"],
    "health":      ["care", "well-being", "healing", "vitality", "balance"],
    "bien-être":   ["sérénité", "équilibre", "vitalité", "harmonie", "ressourcement"],
    "wellness":    ["serenity", "balance", "vitality", "harmony", "renewal"],
    "tech":        ["innovation", "connexion", "intelligence", "automatisation", "fluidité"],
    "saas":        ["efficacité", "automatisation", "collaboration", "données", "fluidité"],
    "mode":        ["style", "élégance", "tendance", "expression", "identité"],
    "fashion":     ["style", "elegance", "trend", "expression", "identity"],
    "luxe":        ["exclusivité", "raffinement", "prestige", "artisanat", "excellence"],
    "luxury":      ["exclusivity", "refinement", "prestige", "craftsmanship", "excellence"],
    "alimentaire": ["authenticité", "saveur", "terroir", "fraîcheur", "convivialité"],
    "restaurant":  ["gastronomie", "convivialité", "saveur", "expérience culinaire", "authenticité"],
    "café":        ["convivialité", "énergie", "authenticité", "rituel", "chaleur"],
    "bio":         ["nature", "authenticité", "durabilité", "pureté", "terroir"],
    "éducation":   ["apprentissage", "progression", "curiosité", "clarté", "savoir"],
    "education":   ["learning", "growth", "curiosity", "clarity", "knowledge"],
    "sport":       ["performance", "énergie", "dépassement", "endurance", "victoire"],
    "fitness":     ["performance", "progression", "endurance", "énergie", "transformation"],
    "immobilier":  ["confiance", "ancrage", "espace", "investissement", "habitat"],
    "créatif":     ["imagination", "originalité", "création", "expression", "singularité"],
    "agence":      ["expertise", "collaboration", "résultats", "stratégie", "créativité"],
    "juridique":   ["confiance", "rigueur", "expertise", "protection", "conseil"],
    "artisanat":   ["savoir-faire", "authenticité", "création", "qualité", "tradition"],
}

_SECTOR_WORDS_TO_AVOID: dict[str, list[str]] = {
    "fitness":     ["Fit", "Track", "Pulse", "Coach", "Gym", "Sport", "Body"],
    "tech":        ["Tech", "App", "Digital", "Smart", "Soft", "Net", "Cloud"],
    "saas":        ["App", "Soft", "Cloud", "Hub", "Suite", "Pro", "Platform"],
    "fintech":     ["Pay", "Cash", "Bank", "Fin", "Money", "Fund", "Trade"],
    "restaurant":  ["Food", "Eat", "Chef", "Cook", "Taste", "Dish", "Meal"],
    "mode":        ["Fashion", "Style", "Wear", "Chic", "Trend", "Look"],
    "immobilier":  ["Immo", "Home", "House", "Real", "Estate", "Property"],
    "santé":       ["Med", "Health", "Care", "Clinic", "Soin", "Bio", "Well"],
    "éducation":   ["Learn", "Edu", "School", "Study", "Class", "Course"],
}

_SECTOR_EXAMPLES: dict[str, dict[str, str]] = {
    "fintech": {
        "descriptive": "VaultEdge", "emotional": "TrustFlow",
        "benefit": "WealthPath", "hybrid": "Fintora", "action": "GrowNow", "brandable": "Finaxi",
    },
    "restaurant": {
        "descriptive": "TableNoire", "emotional": "SavoirFaire",
        "benefit": "BonGoût", "hybrid": "Relvanto", "action": "Déguste", "brandable": "Cuisira",
    },
    "tech": {
        "descriptive": "DataForge", "emotional": "FlowMind",
        "benefit": "AutoBoost", "hybrid": "Nexlify", "action": "BuildNow", "brandable": "Techvara",
    },
    "mode": {
        "descriptive": "MaisonNova", "emotional": "PureForme",
        "benefit": "StylePlus", "hybrid": "Velura", "action": "Revêts", "brandable": "Fabriva",
    },
    "santé": {
        "descriptive": "CliniCare", "emotional": "SerenVie",
        "benefit": "VitalPath", "hybrid": "Sanovia", "action": "Guéris", "brandable": "Healia",
    },
    "éducation": {
        "descriptive": "ClassPath", "emotional": "CuriOs",
        "benefit": "LearnFast", "hybrid": "Eduvara", "action": "Progresse", "brandable": "Scholira",
    },
    "sport": {
        "descriptive": "PeakRun", "emotional": "RiseForce",
        "benefit": "MaxPerf", "hybrid": "Athletra", "action": "Surpasse", "brandable": "Sportiva",
    },
    "immobilier": {
        "descriptive": "PierreLive", "emotional": "HomeHaven",
        "benefit": "SpaceGain", "hybrid": "Residova", "action": "Emménage", "brandable": "Homira",
    },
}

_DEFAULT_THEMES = ["valeur principale de l'offre", "bénéfice client", "différenciation", "identité de la marque"]
_DEFAULT_AVOID = ["Pro", "Plus", "Go", "Hub", "Lab", "Co"]
_DEFAULT_EXAMPLES = {
    "descriptive": "NomDescriptif", "emotional": "NomÉmotionnel",
    "benefit": "NomBénéfice", "hybrid": "NomHybride", "action": "NomAction", "brandable": "NomInventé",
}


def _get_sector_key(sector: str) -> str | None:
    s = (sector or "").lower().strip()
    for key in _SECTOR_THEMES:
        if key in s:
            return key
    return None


def _build_semantic_alignment(sector: str, solution: str, problem: str) -> str:
    key = _get_sector_key(sector)
    themes = _SECTOR_THEMES.get(key, _DEFAULT_THEMES) if key else _DEFAULT_THEMES
    themes_str = "\n".join(f"- {t}" for t in themes)
    solution_hint = ""
    if solution or problem:
        ref = solution or problem
        solution_hint = f"- thèmes ou ton issus de la solution/problème du projet : « {ref[:120]} »"
    return f"""SEMANTIC ALIGNMENT:
Each name MUST reflect at least one of these themes (derived from sector « {sector} ») :
{themes_str}
{solution_hint}
- or themes from USER PREFERENCES (values, personality, desired user feeling)"""


def _build_words_to_avoid(sector: str) -> str:
    key = _get_sector_key(sector)
    words = _SECTOR_WORDS_TO_AVOID.get(key, _DEFAULT_AVOID) if key else _DEFAULT_AVOID
    return ", ".join(words)


def _build_examples(sector: str) -> str:
    key = _get_sector_key(sector)
    ex = _SECTOR_EXAMPLES.get(key, _DEFAULT_EXAMPLES) if key else _DEFAULT_EXAMPLES
    return "\n".join([
        f"    * descriptive ({ex.get('descriptive', 'NomDescriptif')})",
        f"    * emotional ({ex.get('emotional', 'NomÉmotionnel')})",
        f"    * benefit-driven ({ex.get('benefit', 'NomBénéfice')})",
        f"    * hybrid ({ex.get('hybrid', 'NomHybride')})",
        f"    * action-oriented ({ex.get('action', 'NomAction')})",
        f"    * invented/brandable ({ex.get('brandable', 'NomInventé')})",
    ])


# ─────────────────────────────────────────
# USER PROMPT BUILDER
# ─────────────────────────────────────────
def build_name_user_prompt(idea: dict, excluded_names: list = None) -> str:
    idea_name           = idea.get("idea_name", "")
    sector              = idea.get("sector", "")
    target_users        = idea.get("target_users", "")
    problem             = idea.get("problem", "")
    solution_description = idea.get("solution_description", "")
    country             = idea.get("country", "")
    country_code        = idea.get("country_code", "")
    language            = idea.get("language", "fr")

    uv   = _fmt_list(idea.get("user_brand_values"))
    up   = _fmt_list(idea.get("user_personality"))
    uf   = _fmt_list(idea.get("user_feelings"))
    nl   = _fmt_str(idea.get("naming_language"))
    nlen = _fmt_str(idea.get("naming_length"))
    ninc = _fmt_str(idea.get("naming_include"))
    nexc = _fmt_str(idea.get("naming_exclude"))
    remarks_raw = (idea.get("user_remarks") or "").strip()

    founder_remarks_block = ""
    if remarks_raw:
        founder_remarks_block = f"""
FOUNDER REMARKS (régénération / feedback — prioriser avec USER PREFERENCES pour cette salve) :
{remarks_raw}

Traduis ces remarques en contraintes concrètes (ton, sonorité, sémantique, longueur, ce qu'il faut éviter ou favoriser par rapport aux propositions précédentes).
"""

    user_prefs_block = f"""
USER PREFERENCES (founder input — apply to every proposed name, together with CONTEXT above):
- Brand values to convey: {uv}
- Brand personality: {up}
- How users should feel: {uf}
- Naming language preference: {nl}
- Name length preference: {nlen}
- Favor / include (themes or words, if any): {ninc}
- Avoid / exclude (words or themes): {nexc}

If a line is "—", ignore that axis. Otherwise treat it as binding alongside the rules below.
If USER PREFERENCES conflict with generic examples elsewhere in this prompt, prioritize CONTEXT + USER PREFERENCES for meaning and tone.
"""

    blacklist_section = ""
    if excluded_names:
        blacklist_section = f"""
BLACKLIST (these names already exist, NEVER use them):
{chr(10).join(f"- {n}" for n in excluded_names)}
"""

    # Sections dynamiques selon le secteur
    semantic_alignment = _build_semantic_alignment(sector, solution_description, problem)
    words_to_avoid     = _build_words_to_avoid(sector)
    examples_block     = _build_examples(sector)

    # Langue de rédaction des descriptions
    desc_lang = "in the project language" if language != "fr" else "en français uniquement"

    return f"""
CONTEXT:
Idea: {idea_name}
Sector: {sector}
Target users: {target_users}
Problem: {problem}
Solution description: {solution_description}
Country: {country} ({country_code})
Language: {language}

{user_prefs_block}
{founder_remarks_block}
{blacklist_section}

TASK:
Generate 6 UNIQUE and ORIGINAL brand names for this project.
Each name must fit both the STARTUP CONTEXT (sector, solution, target users) and the USER PREFERENCES when specified (non "—").

CRITICAL CONSTRAINTS:
- Names MUST be uncommon and not widely used
- Avoid generic/overused words for this sector: {words_to_avoid}
- Avoid generic patterns: XName, NameX, NamePro, NamePlus, NameGo
- Prefer invented or hybrid words specific to this project
- 1–2 words maximum (NOT 3)
- Easy to pronounce globally
- Use only latin characters (NO accents)

NAMING QUALITY RULES:
- Each name MUST follow a DIFFERENT pattern
- Mix naming styles:
{examples_block}

{semantic_alignment}

ORIGINALITY RULE (VERY IMPORTANT):
- If a name sounds common, generic, or already exists → DO NOT include it
- At least 3 names MUST be invented or hybrid words

OUTPUT FORMAT (STRICT JSON):
{{
  "name_options": [
    {{
      "name": "",
      "description": ""
    }}
  ]
}}

DESCRIPTION LANGUAGE:
- Each "description" MUST be written {desc_lang} (professional tone, 1-2 short sentences: why this name fits the project).

IMPORTANT:
- ONLY valid JSON
- No text outside JSON
- MUST return exactly 6 names
- Do NOT reuse any name from BLACKLIST
"""


# LangGraph create_react_agent: system prompt
NAME_REACT_SYSTEM_PROMPT = """You are a senior branding expert agent. Your goal is to find brand names that are NOT already known brands in Brandfetch (tool returns availability "not_exists").

Tools:
- generate_names(excluded_names_str): Proposes new names. Pass every name you have already generated or seen in any validation (comma-separated). Use an empty string only for the very first generation. This list must grow each round so you never repeat a name.
- validate_names: Call right after generate_names. Pass names_json as the exact string returned by generate_names (valid JSON with name_options), or pass name_options as the list of dicts.

Each round:
1) generate_names(excluded_names_str)
2) validate_names(names_json=<exact output from step 1>)

Track all names from validation results; add them to the exclusion string for the next generate_names call.

Repeat until you have at least {target} distinct names with availability "not_exists", then stop and briefly confirm those names in plain text.

Rules:
- Always validate immediately after each generation.
- Do not call generate_names twice without a validate_names in between.
- If many names are "exists", generate again with an updated exclusion list.
- The generate_names tool embeds founder USER PREFERENCES and any FOUNDER REMARKS for this run; all proposed names must respect startup context, preferences, and remarks.
"""


def build_name_react_user_message(idea_context: dict, *, target: int = NAME_TARGET_COUNT) -> str:
    """Human message for the ReAct graph (system prompt is set on create_react_agent)."""
    idea_name           = idea_context.get("idea_name", "")
    sector              = idea_context.get("sector", "")
    target_users        = idea_context.get("target_users", "")
    problem             = idea_context.get("problem", "")
    solution_description = idea_context.get("solution_description", "")
    country             = idea_context.get("country", "")
    country_code        = idea_context.get("country_code", "")
    language            = idea_context.get("language", "fr")

    uv   = _fmt_list(idea_context.get("user_brand_values"))
    up   = _fmt_list(idea_context.get("user_personality"))
    uf   = _fmt_list(idea_context.get("user_feelings"))
    nl   = _fmt_str(idea_context.get("naming_language"))
    nlen = _fmt_str(idea_context.get("naming_length"))
    ninc = _fmt_str(idea_context.get("naming_include"))
    nexc = _fmt_str(idea_context.get("naming_exclude"))

    prefs_line = (
        f"values={uv}; personality={up}; feelings={uf}; "
        f"naming_lang={nl}; length={nlen}; include={ninc}; exclude={nexc}"
    )

    remarks_raw = (idea_context.get("user_remarks") or "").strip()
    remarks_section = ""
    if remarks_raw:
        remarks_section = f"\nFounder remarks for this run (must clearly steer generate_names output): {remarks_raw}\n"

    return f"""Startup context (the generate_names tool embeds this in its prompt; keep exclusions accurate):
- idea_name: {idea_name}
- sector: {sector}
- target_users: {target_users}
- problem: {problem}
- solution_description: {solution_description}
- country: {country} ({country_code})
- language: {language}

User naming preferences (must be reflected in every generation round): {prefs_line}
{remarks_section}
Objective: at least {target} distinct names with availability not_exists from validate_names.
First step: call generate_names with excluded_names_str="" then validate_names(names_json=<exact JSON string from generate_names>)."""
