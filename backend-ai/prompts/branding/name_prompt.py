def build_name_user_prompt(state) -> str:

    idea = state.clarified_idea or {}
    sector = idea.get("sector") or idea.get("secteur") or state.sector
    target_users = idea.get("target_users") or state.target_audience
    problem = idea.get("problem") or ""
    solution_description = idea.get("solution_description") or idea.get("solution") or ""
    country = idea.get("country") or ""
    country_code = idea.get("country_code") or ""
    language = idea.get("language") or "fr"

    return f"""
CONTEXT:
Idea: {state.name}
Sector: {sector}
Description: {state.description}
Target users: {target_users}
Problem: {problem}
Solution description: {solution_description}
Country: {country} ({country_code})
Language: {language}

Clarified idea:
{idea}

TASK:
Generate up to 10 brand names for this startup.

CONSTRAINTS:
- 1–3 words maximum
- easy to pronounce
- relevant to the idea
- names MUST relate to the provided sector, problem, target users, solution, and country
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
- use clarified fields as primary source of truth
- do not ignore: sector, target_users, problem, solution_description, country
"""