"""
Phase 2.5 — Affinage iteratif du concept creatif (avant generation HTML).

L'utilisateur regarde la description JSON proposee (Phase 2) et formule des
retours en langage naturel : « ajoute une section pricing », « rend le hero
plus minimaliste », « change le ton, plus rassurant »...

Le LLM repart de la description existante + des retours utilisateur et
renvoie une description JSON MISE A JOUR, en respectant strictement le meme
contrat de sortie que Phase 2.
"""

from __future__ import annotations

import json
from typing import Any

from tools.website_builder.brand_context_fetch import BrandContext


WEBSITE_DESCRIPTION_REFINE_SYSTEM = """Tu es Senior Web Designer & Copywriter.

Tu dois faire EVOLUER une description de site vitrine selon les retours de l'utilisateur.
La description contient une ARCHITECTURE (sections, nav, animations) et du CONTENU (textes, icones).
Tu renvoies la description COMPLETE mise a jour avec les modifications demandees.

REGLES :
1) Conserver tout ce qui n'est PAS impacte par les retours.
2) Modifier uniquement ce qui est explicitement demande.
3) Garder la coherence : ids uniques slug minuscule, tous les target_id pointent vers des ids reels.
4) Respecter strictement la langue cible (tout le texte).
5) Aucun lorem ipsum, aucun TODO, aucun placeholder.
6) Contraintes structure (architecture) :
   - hero TOUJOURS premier, footer TOUJOURS dernier, contact OBLIGATOIRE.
   - Entre 5 et 7 sections au total.
   - 2 a 4 animations sobres (fade-in, hover, smooth scroll).
   - Maximum 5 liens dans nav_links.
7) Contraintes contenu :
   - Icones UNIQUEMENT Lucide (kebab-case) : coffee, briefcase, star, mail, phone, map-pin, users, shield, etc.
   - INTERDIT : emojis, icones inventees, URL images externes.
   - Temoignages : initiales + nom + role + texte uniquement, JAMAIS de photo.
   - Visuels : "gradient", "svg_pattern", "logo", "icon_cluster" ou "none" uniquement.
8) user_summary en langue cible, commence par "Voici ce que je vais te creer..." et mentionne les changements.

CONTRAT DE SORTIE — renvoyer EXACTEMENT la meme structure JSON recue, avec les modifications appliquees.
JSON STRICT uniquement, aucun texte autour, sans commentaire.

AUTO-VERIFICATION INTERNE :
- JSON valide et parsable.
- Tous les target_id existent dans sections[*].id de l'architecture.
- Tous les ids sont uniques en slug minuscule.
- Toutes les icones du contenu sont des noms Lucide valides.
- Aucune URL image inventee dans le contenu.
- Aucun texte hors JSON.
"""


def build_description_refine_user_prompt(
    ctx: BrandContext,
    current_description: dict[str, Any],
    user_feedback: str,
) -> str:
    feedback = (user_feedback or "").strip() or "(aucun retour)"
    description_json = json.dumps(current_description, ensure_ascii=False, indent=2)

    return f"""LANGUE CIBLE : {ctx.language}

CONTEXTE PROJET (a respecter) :
- Nom du projet : {ctx.project_name}
- Marque : {ctx.brand_name}
- Slogan : {ctx.slogan or "(aucun slogan)"}
- Secteur : {ctx.sector or "(non precise)"}
- Public cible : {ctx.target_audience or "(non precise)"}
- Pitch : {ctx.short_pitch or "(non fourni)"}
- Brief : {ctx.description_brief or "(non fournie)"}

DESCRIPTION ACTUELLE DU SITE (a faire evoluer, JSON) :
{description_json}

RETOURS DE L'UTILISATEUR (a appliquer precisement) :
\"\"\"{feedback}\"\"\"

TACHE :
- Met a jour la description ci-dessus selon les retours.
- Conserve tout le reste a l'identique.
- Renvoie UNIQUEMENT le JSON complet resultant, conforme au schema systeme.
- `user_summary` doit decrire en 4-6 phrases ce que tu vas creer APRES tes retours,
  en commencant par "Voici ce que je vais te creer..." et en mentionnant les
  changements appliques.
"""
