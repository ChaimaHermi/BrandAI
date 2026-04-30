"""
Prompts pour SloganAgent : contexte projet (idée clarifiée) + nom choisi + préférences utilisateur one-shot.
"""

from config.branding_config import SLOGAN_TARGET_COUNT


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


SLOGAN_SYSTEM_PROMPT = """Tu es un·e rédacteur·rice senior en branding et copywriting.
Tu génères des slogans percutants, mémorables et crédibles pour une marque.

Règles strictes :
- Réponds UNIQUEMENT par un JSON valide, sans markdown ni texte avant/après.
- La structure exacte est imposée dans le message utilisateur.
- Chaque slogan doit être distinct (pas de variantes quasi identiques).
- Ne reproduis ni n’imite de slogans déjà connus (grandes marques, concurrents directs, campagnes célèbres). Invente des formulations originales ; évite les tournures ou phrases quasi identiques à des accroches existantes ou déposées.
- Évite les clichés vides (« leader », « innovation », « révolutionnaire », « simple », « facile ») sauf si le contexte l’exige vraiment.
- Le champ « rationale » doit être écrit dans la même langue que le slogan (langue de rédaction du projet).
"""


def build_slogan_user_prompt(
    idea: dict,
    brand_name: str,
    preferences: dict | None,
    *,
    target: int = SLOGAN_TARGET_COUNT,
) -> str:
    """
    idea: clarified_idea (secteur, cible, problème, solution, pays, langue…).
    brand_name: nom de marque retenu par l'utilisateur.
    preferences: dict flat depuis le front (positionnement, listes, longueur, langue, mots_eviter).
    """
    idea_name = idea.get("idea_name", "")
    sector = idea.get("sector", "")
    target_users = idea.get("target_users", "")
    problem = idea.get("problem", "")
    solution_description = idea.get("solution_description", "")
    pitch = idea.get("short_pitch", "") or ""
    country = idea.get("country", "")
    country_code = idea.get("country_code", "")
    language = idea.get("language", "fr")

    prefs = preferences or {}
    pos = _fmt_str(prefs.get("positionnement"))
    st = _fmt_list(prefs.get("style_ton_slogan") or prefs.get("slogan_style_tones"))
    usp = _fmt_list(prefs.get("message_usp"))
    fmt = _fmt_list(prefs.get("format"))
    ling = _fmt_list(prefs.get("style_linguistique"))
    longueur = _fmt_str(prefs.get("longueur"))
    langue_redac = _fmt_str(prefs.get("langue"))
    eviter = _fmt_str(prefs.get("mots_eviter"))
    rem_txt = (prefs.get("user_remarks") or "").strip()

    remarques_block = ""
    if rem_txt:
        remarques_block = f"""
REMARQUES DU CLIENT (pour cette génération ou régénération — à intégrer en plus des préférences ci-dessous) :
{rem_txt}
"""

    return f"""CONTEXTE PROJET (idée clarifiée) :
- Nom working / idée : {idea_name}
- Secteur : {sector}
- Public cible : {target_users}
- Problème adressé : {problem}
- Solution / offre : {solution_description}
- Pitch court (si dispo) : {pitch}
- Pays : {country} ({country_code})
- Langue du projet : {language}

NOM DE MARQUE CHOISI (à utiliser dans les slogans si pertinent, ou à évoquer implicitement) :
{brand_name}

PRÉFÉRENCES UTILISATEUR (à respecter ; « — » = non précisé, alors tu restes cohérent avec le contexte) :
- Positionnement principal : {pos}
- Style / ton du slogan : {st}
- Messages / USP à faire passer : {usp}
- Formats souhaités (affirmation, promesse, question, etc.) : {fmt}
- Styles linguistiques : {ling}
- Longueur cible : {longueur}
- Langue de rédaction du slogan : {langue_redac}
- Mots ou expressions à éviter : {eviter}
{remarques_block}
TÂCHE :
Propose exactement {target} slogans distincts pour la marque « {brand_name} », alignés sur le CONTEXTE PROJET et les PRÉFÉRENCES ci-dessus.
Chaque slogan doit être prêt à l'emploi (ponctuation légère autorisée ; pas de guillemets dans le texte du slogan).

FORMAT DE SORTIE (JSON strict uniquement) :
{{
  "slogan_options": [
    {{
      "text": "…",
      "rationale": "…"
    }}
  ]
}}

Exigences :
- Exactement {target} entrées dans slogan_options.
- Clés uniquement : text, rationale.
- Pas de caractères spéciaux parasites ni de retours ligne dans « text » (une phrase ou une courte accroche).
- Aucun slogan copié ou dérivé trop proche d’un slogan publicitaire existant ; proposer uniquement des textes originaux pour cette marque.
"""
