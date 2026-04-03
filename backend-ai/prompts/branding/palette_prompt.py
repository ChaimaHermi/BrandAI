"""
Prompts pour PaletteAgent : idée clarifiée + nom de marque + préférences couleur (3 palettes distinctes).
"""

from config.branding_config import PALETTE_TARGET_COUNT


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


PALETTE_SYSTEM_PROMPT = """Tu es un·e directeur·rice artistique senior en identité visuelle et design de marque.
Tu proposes des palettes de couleurs cohérentes, distinctes et utilisables (web & print).

Règles strictes :
- Réponds UNIQUEMENT par un JSON valide, sans markdown ni texte avant/après.
- La structure exacte est imposée dans le message utilisateur.
- Chaque palette doit être clairement différente (ambiances ou codes couleur non redondants).
- N’imite pas des palettes signature de grandes marques connues ; invente des combinaisons originales adaptées au contexte.
- Couleurs en hexadécimal #RRGGBB uniquement (6 chiffres hex après #).
- Pense accessibilité : au moins une combinaison texte/fond plausible pour l’UI (contraste raisonnable).
- Les champs « rationale » en français : courte phrase (pourquoi cette teinte dans cette palette).
"""


def build_palette_user_prompt(
    idea: dict,
    brand_name: str,
    preferences: dict | None,
    *,
    slogan_hint: str = "",
    target: int = PALETTE_TARGET_COUNT,
) -> str:
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
    ambiance = _fmt_str(prefs.get("ambiance"))
    style_color = _fmt_list(prefs.get("style_couleur") or prefs.get("style_color"))
    contraste = _fmt_str(prefs.get("contraste") or prefs.get("niveau_contraste"))
    eviter = _fmt_str(prefs.get("couleurs_eviter") or prefs.get("mots_eviter"))
    rem_txt = (prefs.get("user_remarks") or "").strip()

    slogan_block = ""
    if (slogan_hint or "").strip():
        slogan_block = f"""
SLOGAN / MESSAGE (contexte optionnel pour harmoniser le ton visuel) :
{(slogan_hint or "").strip()}
"""

    remarques_block = ""
    if rem_txt:
        remarques_block = f"""
REMARQUES DU CLIENT (génération ou régénération) :
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
- Langue clarifier : {language}

NOM DE MARQUE (aligner les couleurs sur cette identité) :
{brand_name}
{slogan_block}
PRÉFÉRENCES COULEUR ( « — » = non précisé ; reste cohérent avec le contexte projet ) :
- Ambiance générale : {ambiance}
- Styles / directions colorimétriques : {style_color}
- Contraste souhaité : {contraste}
- Couleurs ou teintes à éviter : {eviter}
{remarques_block}
TÂCHE :
Propose exactement {target} palettes de couleurs DISTINCTES pour la marque « {brand_name} », chacune alignée sur le CONTEXTE PROJET ci-dessus.
Chaque palette doit contenir entre 4 et 6 couleurs nommées avec rôles (primary, secondary, accent, neutral, background, etc.).

FORMAT DE SORTIE (JSON strict uniquement) :
{{
  "palette_options": [
    {{
      "palette_name": "…",
      "swatches": [
        {{
          "name": "…",
          "hex": "#RRGGBB",
          "role": "primary|secondary|accent|neutral|background|text",
          "rationale": "…"
        }}
      ]
    }}
  ]
}}

Exigences :
- Exactement {target} entrées dans palette_options.
- Chaque swatch : name, hex, role, rationale ; hex strictement # + 6 caractères hex.
- Les trois palettes doivent offrir des directions visuelles différentes tout en restant crédibles pour le secteur et la cible.
"""
