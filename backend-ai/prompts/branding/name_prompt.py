from langchain_core.prompts import PromptTemplate

from config.branding_config import NAME_TARGET_COUNT


# ─────────────────────────────────────────
# REACT AGENT PROMPT
# ─────────────────────────────────────────
REACT_AGENT_PROMPT = PromptTemplate.from_template("""
You are a senior branding expert.
Your goal: find at least 3 brand names that do NOT exist yet.

You have access to these tools:
{tools}

Tool names available: {tool_names}

Use EXACTLY this format:

Thought: what I need to do
Action: tool_name
Action Input: input for the tool
Observation: tool result
... (repeat until you have 3 available names)
Thought: I found 3 available names, objective reached
Final Answer: valid JSON list of 3 available names

Rules:
- ALWAYS call generate_names first
- ALWAYS call validate_names after generating
- NEVER reuse blacklisted names
- STOP only when you have at least 3 not_exists names
- Final Answer MUST be valid JSON like:
[
  {{"name": "...", "description": "...", "availability": "not_exists"}},
  {{"name": "...", "description": "...", "availability": "not_exists"}},
  {{"name": "...", "description": "...", "availability": "not_exists"}}
]

Question: {input}
{agent_scratchpad}
""")


# ─────────────────────────────────────────
# USER PROMPT BUILDER
# ─────────────────────────────────────────
def build_name_user_prompt(idea: dict, excluded_names: list = None) -> str:

    idea_name = idea.get("idea_name", "")
    sector = idea.get("sector", "")
    target_users = idea.get("target_users", "")
    problem = idea.get("problem", "")
    solution_description = idea.get("solution_description", "")
    country = idea.get("country", "")
    country_code = idea.get("country_code", "")
    language = idea.get("language", "fr")

    blacklist_section = ""
    if excluded_names:
        blacklist_section = f"""
BLACKLIST (these names already exist, NEVER use them):
{chr(10).join(f"- {n}" for n in excluded_names)}
"""

    return f"""
CONTEXT:
Idea: {idea_name}
Sector: {sector}
Target users: {target_users}
Problem: {problem}
Solution description: {solution_description}
Country: {country} ({country_code})
Language: {language}

{blacklist_section}

TASK:
Generate 6 UNIQUE and ORIGINAL brand names for this startup.

CRITICAL CONSTRAINTS:
- Names MUST be uncommon and not widely used
- Avoid common words: Fit, Track, Pulse, Coach, App, Pro, Tech
- Avoid common patterns: XFit, FitX, XTrack, TrackX, CoachPro
- Prefer invented or hybrid words (e.g., Movira, Fitnex, Trainly)
- 1–2 words maximum (NOT 3)
- easy to pronounce globally
- use only latin characters (NO accents)

NAMING QUALITY RULES:
- each name MUST follow a DIFFERENT pattern
- mix naming styles:
    * descriptive (HomeCoach)
    * emotional (RiseFlow)
    * benefit-driven (DailyBoost)
    * hybrid (Trainlyx)
    * action-oriented (MoveUp)
    * invented/brandable (Movira, Fitnex)

SEMANTIC ALIGNMENT:
Each name MUST reflect at least one of:
- motivation
- coaching
- progress tracking
- habit building
- home training

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

DESCRIPTION LANGUAGE (mandatory):
- Each "description" MUST be written in French only (ton professionnel, 1-2 phrases courtes: pourquoi ce nom convient au projet).
- Les champs "name" suivent les regles ci-dessus (latin, sans accents, etc.); ne traduis pas les noms de marque en francais si ce sont des mots inventes.

IMPORTANT:
- ONLY valid JSON
- no text outside JSON
- MUST return exactly 6 names
- do NOT reuse any name from BLACKLIST
"""


# LangGraph create_react_agent: system prompt (tool-calling, not legacy text ReAct)
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
"""


def build_name_react_user_message(idea_context: dict, *, target: int = NAME_TARGET_COUNT) -> str:
    """Human message for the ReAct graph (system prompt is set on create_react_agent)."""
    idea_name = idea_context.get("idea_name", "")
    sector = idea_context.get("sector", "")
    target_users = idea_context.get("target_users", "")
    problem = idea_context.get("problem", "")
    solution_description = idea_context.get("solution_description", "")
    country = idea_context.get("country", "")
    country_code = idea_context.get("country_code", "")
    language = idea_context.get("language", "fr")
    return f"""Startup context (the generate_names tool already embeds this in its prompt; keep exclusions accurate):
- idea_name: {idea_name}
- sector: {sector}
- target_users: {target_users}
- problem: {problem}
- solution_description: {solution_description}
- country: {country} ({country_code})
- language: {language}

Objective: at least {target} distinct names with availability not_exists from validate_names.
First step: call generate_names with excluded_names_str="" then validate_names(names_json=<exact JSON string from generate_names>)."""