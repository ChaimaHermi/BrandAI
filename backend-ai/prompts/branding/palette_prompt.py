"""
Prompts pour PaletteAgent : uniquement l’idée clarifiée + nom de marque.
L’IA propose exactement 3 palettes alignées sur le contexte projet (secteur, cible, problème, solution, etc.).
"""

from config.branding_config import PALETTE_TARGET_COUNT


PALETTE_SYSTEM_PROMPT = f"""Tu es un·e directeur·rice artistique senior en identité visuelle et design de marque.
Tu proposes des palettes de couleurs cohérentes, distinctes et utilisables (web & print), déduites uniquement du contexte projet fourni.

Règles strictes :
- Réponds UNIQUEMENT par un JSON valide, sans markdown ni texte avant/après.
- Tu dois produire EXACTEMENT {PALETTE_TARGET_COUNT} palettes dans le tableau « palette_options », ni plus ni moins.
- La structure exacte est imposée dans le message utilisateur.
- Chaque palette doit être clairement différente (ambiances ou codes couleur non redondants).
- N’imite pas des palettes signature de grandes marques connues ; invente des combinaisons originales adaptées au secteur et à la cible décrits dans le contexte.
- Couleurs en hexadécimal #RRGGBB uniquement (6 chiffres hex après #).
- Pense accessibilité : au moins une combinaison texte/fond plausible pour l’UI (contraste raisonnable).
- Chaque palette inclut « palette_description » en français : 1 à 3 phrases expliquant pourquoi cette direction couleur colle au secteur, à la cible et au positionnement.
- Les champs « rationale » (par swatch) en français : courte phrase (rôle de la teinte dans la palette).
"""


def build_palette_user_prompt(
    idea: dict,
    brand_name: str,
    *,
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

    return f"""IDÉE CLARIFIÉE (contexte unique — base toute ta proposition dessus) :
- Nom working / idée : {idea_name}
- Secteur : {sector}
- Public cible : {target_users}
- Problème adressé : {problem}
- Solution / offre : {solution_description}
- Pitch court (si dispo) : {pitch}
- Pays : {country} ({country_code})
- Langue : {language}

NOM DE MARQUE (les palettes doivent habiller cette identité) :
{brand_name}

TÂCHE :
À partir UNIQUEMENT de l’idée clarifiée ci-dessus, propose EXACTEMENT {target} palettes de couleurs DISTINCTES pour la marque « {brand_name} » (ni une de moins, ni une de plus).
Chaque palette doit être crédible pour le secteur et la cible, avec des directions visuelles différentes (sans répéter la même ambiance).
Chaque palette contient entre 4 et 6 couleurs nommées avec rôles (primary, secondary, accent, neutral, background, text, etc.).

FORMAT DE SORTIE (JSON strict uniquement) :
{{
  "palette_options": [
    {{
      "palette_name": "…",
      "palette_description": "Pourquoi cette palette colle au projet (secteur, cible, positionnement) — 1 à 3 phrases en français.",
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
- Le tableau « palette_options » contient EXACTEMENT {target} objets (pour ce brief : {target} = nombre imposé, pas d’entrée supplémentaire).
- Chaque palette : palette_name, palette_description (argumentaire court), swatches.
- Chaque swatch : name, hex, role, rationale ; hex strictement # + 6 caractères hex.
- Les {target} palettes doivent être alignées sur l’idée clarifiée (secteur, public, problème, solution).
"""
