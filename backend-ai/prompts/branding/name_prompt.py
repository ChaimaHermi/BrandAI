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
Generate 3 to 5 brand names.

CONSTRAINTS:
- 1–2 words max
- easy to pronounce
- modern and startup-friendly
- relevant to the idea

FOR EACH NAME:
- include a short explanation (max 8 words)
- explain WHY the name fits

OUTPUT FORMAT (STRICT JSON):

{{
  "name_options": [
    {{
      "name": "",
      "description": ""
    }}
  ]
}}
"""