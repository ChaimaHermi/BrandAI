"""
Prompts pour l’extraction structurée de mots-clés (analyse de marché).
"""


def _fmt(s: str | None) -> str:
    t = (s or "").strip()
    return t if t else "—"


def build_keyword_extraction_user_prompt(idea: dict) -> str:
    """Construit le message utilisateur (idée + schéma JSON attendu)."""
    return f"""Voici une idée de projet :

PITCH : {_fmt(idea.get("short_pitch"))}
DESCRIPTION : {_fmt(idea.get("solution_description"))}
PROBLÈME RÉSOLU : {_fmt(idea.get("problem"))}
UTILISATEURS CIBLES : {_fmt(idea.get("target_users"))}
SECTEUR : {_fmt(idea.get("sector"))}
PAYS CIBLE : {_fmt(idea.get("country_code"))}

Génère les mots-clés pour analyser ce marché selon ce schéma JSON exact :

{{
  "primary_keywords": [
    "<mot-clé principal exact que les utilisateurs tapent dans Google>"
  ],
  "market_keywords": [
    "<termes pour mesurer la taille et la croissance du marché>"
  ],
  "competitor_search_queries": [
    "<requêtes pour trouver les concurrents directs>"
  ],
  "voc_keywords": [
    "<termes que les utilisateurs insatisfaits utilisent pour se plaindre>"
  ],
  "trend_keywords": [
    "<termes pour suivre les tendances et l'évolution du secteur>"
  ],
  "sector_tags": [
    "<catégories sectorielles standardisées pour les APIs>"
  ]
}}

Contraintes par catégorie :
- primary_keywords : 5 termes max, ce que les utilisateurs cherchent vraiment
- market_keywords : 4 termes max, orientés taille/croissance marché
- competitor_search_queries : 4 requêtes max, format "best X software" ou "top X tools"
- voc_keywords : 5 termes max, pain points réels que les gens postent sur Reddit/forums
- trend_keywords : 4 termes max, pour News APIs et Google Trends
- sector_tags : 3 tags max, catégories standardisées (ex: "SaaS", "Productivity", "AI Tools")

Retourne UNIQUEMENT le JSON, rien d'autre.
"""


KEYWORD_EXTRACTOR_SYSTEM_PROMPT = """Tu es un expert en analyse de marché et en recherche sectorielle.
Tu reçois la description d'une idée de projet et tu dois extraire les mots-clés
les plus pertinents pour analyser son marché.

Règles STRICTES :
- Extraire uniquement des mots-clés qui existent réellement sur le marché
- Ne jamais inventer des termes qui ne seraient pas utilisés par les vrais utilisateurs
- Les mots-clés doivent être en anglais (pour maximiser les résultats d'API)
- Chaque catégorie a un rôle précis — respecte la structure demandée
- Répondre UNIQUEMENT en JSON valide, sans markdown, sans backticks, sans texte avant ou après
"""
