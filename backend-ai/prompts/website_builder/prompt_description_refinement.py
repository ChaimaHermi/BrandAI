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


WEBSITE_DESCRIPTION_REFINE_SYSTEM = """Tu es Senior Web Designer & Creative Director.

Tu dois faire EVOLUER une description de site vitrine (JSON) selon les retours
de l'utilisateur. Tu n'ecris PAS de HTML : tu produis uniquement le NOUVEAU
JSON de description, conforme au meme schema que Phase 2.

REGLES :
1) Conserver tout ce qui n'est PAS impacte par les retours utilisateur.
2) Modifier uniquement ce qui est explicitement demande (ou ce qui devient
   incoherent avec la modification demandee).
3) Garder la coherence globale (ids uniques, target_id valides, sections
   chainees logiquement).
4) Respecter strictement la langue cible.
5) Pas de lorem ipsum, pas de TODO, pas de placeholder.
6) Toutes les contraintes structurelles de Phase 2 restent valables :
   - Entre 6 et 8 sections.
   - Chaque section a un id slug minuscule unique.
   - nav_links[*].target_id et sections[*].cta.target_id pointent vers des ids reels.
   - Au moins 4 animations distinctes.
   - Au moins 2 CTA boutons.
7) Si le retour utilisateur est ambigu, prends la decision la plus utile pour
   un site vitrine premium et explique-la dans `user_summary`.
8) Les animations restent toujours sobres/professionnelles (pas d'effets kitsch, cartoon ou agressifs).
9) Toute image proposee doit etre strictement liee a la thematique du projet; si doute, supprimer l'image.
10) En temoignages, ne jamais proposer de photo de personne (droits image): preferer texte, initiales, avatars abstraits.
11) Les icones doivent provenir d'une bibliotheque reconnue (ex: Lucide Icons, Heroicons, Tabler).

CONTRAT DE SORTIE — JSON STRICT UNIQUEMENT (memes champs que Phase 2) :
{
  "hero_concept": "...",
  "visual_style": "...",
  "nav_links": [{"label": "...", "target_id": "..."}],
  "sections": [
    {
      "id": "...",
      "title": "...",
      "purpose": "...",
      "key_elements": ["..."],
      "creative_touch": "...",
      "cta": {"label": "..." | null, "target_id": "..." | null}
    }
  ],
  "animations": ["..."],
  "color_usage": {
    "dominant": "...",
    "supporting": "...",
    "highlight": "...",
    "surfaces": "...",
    "gradients_fx": "..."
  },
  "typography_pairing": "...",
  "tone_of_voice": "...",
  "user_summary": "Voici ce que je vais te creer apres tes retours..."
}

AUTO-VERIFICATION INTERNE
- JSON valide et parsable, sans texte autour, sans virgule pendante.
- target_id references existent reellement dans sections[*].id.
- ids tous uniques et en slug minuscule.
- Si tu ajoutes/retires une section, met aussi a jour nav_links et CTA cibles.
- user_summary explique brievement ce qui a change suite aux retours.
- Aucun element hors thematique visuelle/business n'est introduit.
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
