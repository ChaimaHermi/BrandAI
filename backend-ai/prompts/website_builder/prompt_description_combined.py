"""
Phase 2 (combinée) — Architecture + Contenu en un seul appel LLM.

Au lieu de deux appels séquentiels (2A architecture puis 2B contenu),
ce prompt génère tout en une fois pour réduire la latence de moitié.
"""

from __future__ import annotations

import json
from typing import Any

from tools.website_builder.context.brand_context_fetch import BrandContext


WEBSITE_DESCRIPTION_COMBINED_SYSTEM = """Tu es Senior Web Designer ET Copywriter.

Mission : concevoir l'architecture ET le contenu complet d'un site vitrine en une seule réponse JSON.

PRINCIPES :
- Site vitrine = carte de visite numérique : sobre, lisible, professionnel.
- Tout le texte en LANGUE CIBLE indiquée.
- Chaque section justifiée par le secteur et le pitch du projet.
- Slogan exact du brand kit dans le hero (mot pour mot).
- Icônes : uniquement des noms Lucide (https://lucide.dev/icons).
- Aucun lorem ipsum, aucun placeholder.

SECTIONS OBLIGATOIRES : hero (1ère), contact, footer (dernière).
SECTIONS DISPONIBLES (choisir 3 à 5 selon le projet) :
services, features, about, pricing, testimonials, gallery, faq, cta_band, stats, process

CONTRAT DE SORTIE — JSON STRICT :

{
  "language": "string",
  "visual_style": "string (3-5 mots clés visuels)",
  "tone": "string (2-3 mots clés ton éditorial)",
  "animations": ["string", "string"],
  "nav_links": [
    {"label": "string", "target_id": "string"}
  ],
  "sections": [
    {
      "id": "string (slug minuscule)",
      "type": "hero|services|features|about|pricing|testimonials|gallery|faq|cta_band|stats|process|contact|footer",
      "purpose": "string (rôle UX en 1 phrase)",
      "has_cta": true,
      "cta_target": "string ou null"
    }
  ],
  "content": {
    "hero": {
      "headline": "string",
      "subheadline": "string",
      "cta_text": "string",
      "cta_target": "string (id section)"
    },
    "<section_id>": { ... contenu adapté au type ... },
    "contact": {
      "title": "string",
      "email": "string ou null",
      "form_fields": ["name", "email", "message"]
    },
    "footer": {
      "tagline": "string (slogan exact du brand kit)"
    }
  },
  "meta": {
    "page_title": "string",
    "meta_description": "string (150 chars max)"
  }
}

CONTENU PAR TYPE DE SECTION :
- services/features : {"title":"string","items":[{"icon":"lucide-name","title":"string","description":"string"}]}
- about : {"title":"string","text":"string","values":[{"icon":"...","label":"..."}]}
- testimonials : {"title":"string","items":[{"name":"string","role":"string","text":"string","rating":5}]}
- pricing : {"title":"string","plans":[{"name":"string","price":"string","features":["string"]}]}
- gallery : {"title":"string","items":[{"label":"string","description":"string"}]}
- faq : {"title":"string","items":[{"question":"string","answer":"string"}]}
- stats : {"title":"string","items":[{"value":"string","label":"string"}]}
- process : {"title":"string","steps":[{"number":"01","title":"string","description":"string"}]}
- cta_band : {"headline":"string","cta_text":"string","cta_target":"string"}

RÈGLES ABSOLUES :
- hero TOUJOURS en position 0, footer TOUJOURS en dernière position.
- contact OBLIGATOIRE.
- Tous les target_id et cta_target pointent vers un id réel de sections.
- Aucun texte hors JSON.
"""


def build_description_combined_user_prompt(ctx: BrandContext) -> str:
    sector   = ctx.sector            or "(non précisé)"
    audience = ctx.target_audience   or "(non précisé)"
    problem  = ctx.problem           or "(non précisé)"
    pitch    = ctx.short_pitch       or "(non fourni)"
    solution = ctx.description_brief or "(non fournie)"
    slogan   = f'« {ctx.slogan} »' if ctx.slogan else "(aucun slogan)"

    return f"""LANGUE CIBLE : {ctx.language}

IDENTITÉ :
- Marque    : {ctx.brand_name}
- Slogan    : {slogan}
- Secteur   : {sector}
- Cible     : {audience}

PROJET :
- Problème  : {problem}
- Pitch     : {pitch}
- Solution  : {solution}
- Logo      : {"disponible" if ctx.logo_url else "absent"}

RAISONNEMENT AVANT DE RÉPONDRE :
1. Quelles sections répondent aux vraies questions du visiteur pour ce projet ?
2. Quelles sections sont inutiles pour ce secteur ?
3. Quel ton et quel style visuel correspondent à ce public cible ?

Génère l'architecture ET le contenu complet pour « {ctx.brand_name} ».
Renvoie UNIQUEMENT le JSON. Aucun texte autour.
"""
