def build_name_user_prompt(state) -> str:

    idea = state.clarified_idea or {}

    idea_name = idea.get("idea_name", "")
    sector = idea.get("sector", "")
    target_users = idea.get("target_users", "")
    problem = idea.get("problem", "")
    solution_description = idea.get("solution_description", "")
    country = idea.get("country", "")
    country_code = idea.get("country_code", "")
    language = idea.get("language", "fr")

    return f"""
CONTEXT:
Idea: {idea_name}
Sector: {sector}
Target users: {target_users}
Problem: {problem}
Solution description: {solution_description}
Country: {country} ({country_code})
Language: {language}

TASK:
Generate up to 10 brand names for this startup.

CORE OBJECTIVE:
Create high-quality startup names that are:
- distinctive
- memorable
- meaningful
- brandable and scalable internationally

CONSTRAINTS:
- 1–3 words maximum
- easy to pronounce globally
- relevant to idea, users, and problem
- avoid abstract/fantasy names (Velorum, Nexarion)
- avoid generic names (Cash, Budget, App, Solution)
- avoid repeating same prefix (Fit, Coach, etc.)
- avoid adding country code like TN in most names
- use only latin characters (NO accents)

NAMING QUALITY RULES (CRITICAL):
- each name MUST follow a DIFFERENT pattern
- avoid similar structures (FitX, FitY, FitZ)
- mix naming styles:
    * descriptive (HomeCoach)
    * emotional (RisePulse)
    * benefit-driven (DailyBoost)
    * hybrid (TrainFlow)
    * action-oriented (MoveUp)
- at least 50% of names must NOT contain "fit" or "coach"

BRANDABILITY RULES:
- names must sound like real startups (not keywords)
- avoid overly common single words (Daily, Home, Move alone)
- prefer slightly distinctive or combined words
- must be easy to remember after one read
- must be usable as product/app name


SEMANTIC ALIGNMENT:
Each name MUST clearly reflect at least one of:
- motivation
- coaching
- progress tracking
- habit building
- home training

FOR EACH NAME:
- include a short explanation (max 10 words)
- explanation must clearly justify the name

FINAL SELECTION (VERY IMPORTANT):
- you MUST select exactly 3 best names
- mark them with: "top_choice": true
- all other names must have: "top_choice": false
- there must be EXACTLY 3 top_choice = true

SELECTION CRITERIA:
- memorability
- uniqueness
- brand potential
- clarity of meaning

OUTPUT FORMAT (STRICT JSON):

{{
  "name_options": [
    {{
      "name": "",
      "description": "",
      "top_choice": false
    }}
  ]
}}

IMPORTANT:
- ONLY valid JSON
- no text outside JSON
- NEVER omit "top_choice"
- "top_choice" MUST be boolean (true/false)
- MUST return at least 5 names
- MUST return exactly 3 top_choice=true
"""