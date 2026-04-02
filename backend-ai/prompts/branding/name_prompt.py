def build_name_user_prompt(state) -> str:

    idea = state.clarified_idea or {}

    return f"""
CONTEXT:
Idea: {state.name}
Sector: {state.sector}
Description: {state.description}
Target: {state.target_audience}

Clarified idea:
{idea}

TASK:
Generate up to 10 brand names for this startup.

CONSTRAINTS:
- 1–3 words maximum
- easy to pronounce
- relevant to the idea
- names MUST relate to finance, budget, money, or student life
- prioritize meaningful and semi-descriptive names
- avoid completely abstract or fantasy-like names (e.g. Velorum, Nexarion)
- avoid overly generic names (e.g. Cash, Budget, Fin)
- create hybrid or combined words when possible (e.g. BudgFlow, SpendWise)
- allow slightly longer names if they improve meaning and uniqueness
- use only standard latin characters (NO accents)

NAMING STYLE:
- modern, startup-ready, and memorable
- should clearly hint at the product purpose
- should be usable as a domain name
- balance creativity AND meaning

LANGUAGE:
- descriptions MUST be in French
- descriptions must be natural and correct sentences
- no fragments
- no comma-separated phrases

FOR EACH NAME:
- include a short explanation (max 10 words)
- clearly explain WHY the name fits the idea

OUTPUT FORMAT (STRICT JSON ONLY):

{{
  "name_options": [
    {{
      "name": "",
      "description": ""
    }}
  ]
}}

IMPORTANT:
- return ONLY valid JSON
- do not return empty response
- do not add explanations outside JSON
- if unsure, still return valid JSON
"""