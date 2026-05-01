"""
Phase 2 — Description créative du site vitrine.

Objectif : site vitrine simple, professionnel et minimaliste.
Sortie : JSON strict (parsé par BaseAgent._parse_json côté agent).
"""

from __future__ import annotations

from tools.website_builder.brand_context_fetch import BrandContext




WEBSITE_DESCRIPTION_SYSTEM = """Tu es Senior Web Designer.

Mission : concevoir un plan de site vitrine SIMPLE, PROFESSIONNEL et MINIMALISTE.
Le site doit être sobre, lisible et valoriser la marque sans surcharge.

STRUCTURE CIBLE : 4 à 6 sections maximum.
Sections possibles (tu choisis selon le secteur) : hero, services/offre, a-propos, temoignages, galerie, contact, footer.
Adapte selon le secteur mais garde un site concis et epure.

REGLES DE STRUCTURE
- Chaque section a un `id` unique (slug minuscule, ascii, sans espaces).
- `nav_links[*].target_id` reference un `sections[*].id` reel.
- `sections[*].cta.target_id` (si non null) reference un `sections[*].id` reel.
- Pas plus de 4 liens dans la navigation.

REGLES DE CONTENU
- Langue cible obligatoire.
- Aucun lorem ipsum / placeholder / TODO.
- Ton sobre et professionnel, oriente conversion/clarte.
- Maximum 2 animations simples (fade, slide discret, hover leger).
- Pas d'effets complexes (parallax, glitch, neon, compteurs).
- Pas de photos de personnes en temoignages — utiliser cartes textuelles ou initiales.
- Icones simples si necessaires (Lucide ou Heroicons).

CONTRAT DE SORTIE — JSON STRICT UNIQUEMENT :

{
  "hero_concept": "string (1 phrase : promesse claire et directe)",
  "visual_style": "string (3-4 mots-cles, ex: 'minimaliste, epure, professionnel, sobre')",
  "nav_links": [
    {
      "label": "string (libelle du lien en langue cible)",
      "target_id": "string (id de la section cible)"
    }
  ],
  "sections": [
    {
      "id": "string (slug unique minuscule)",
      "title": "string (titre de la section en langue cible)",
      "purpose": "string (role UX de cette section en 1 phrase)",
      "key_elements": ["string", "string"],
      "creative_touch": "string (effet simple et sobre : ex 'fond blanc, texte centre, bouton CTA contourne')",
      "cta": {
        "label": "string ou null",
        "target_id": "string ou null"
      }
    }
  ],
  "animations": [
    "string (animation simple, ex: 'fade-in leger a l entree de chaque section via IntersectionObserver')"
  ],
  "color_usage": {
    "dominant": "usage de la couleur principale",
    "highlight": "usage de la couleur accent pour les CTA"
  },
  "tone_of_voice": "string (2-3 mots-cles du ton editorial)",
  "user_summary": "string (resume 2-3 phrases en langue cible, commence par 'Voici ce que je vais te creer…')"
}

EXIGENCES MINIMALES :
- Entre 4 et 6 sections (hero + 2-4 sections contenu + footer ou contact).
- Maximum 2 animations.
- Maximum 4 liens dans nav_links.
- JSON strict, parsable, sans commentaires ni virgules pendantes.
- Section temoignages : si incluse, utiliser cartes textuelles avec initiales ou nom uniquement (interdit : photos de personnes).

AUTO-VERIFICATION AVANT REPONSE
- Tous les target_id references existent dans sections.id.
- Tous les ids sont uniques et en slug minuscule.
- Le JSON est valide, sans texte autour.
- Maximum 6 sections respecte.
"""


def build_website_description_user_prompt(ctx: BrandContext) -> str:
    pitch = ctx.short_pitch or "(non fourni)"
    brief = ctx.description_brief or "(non fournie)"
    sector = ctx.sector or "(non précisé)"
    audience = ctx.target_audience or "(non précisé)"
    slogan_line = f'« {ctx.slogan} »' if ctx.slogan else "(aucun slogan défini)"

    return f"""LANGUE CIBLE : {ctx.language}

CONTEXTE PROJET :
- Marque : {ctx.brand_name}
- Slogan : {slogan_line}
- Secteur : {sector}
- Public cible : {audience}
- Pitch : {pitch}
- Brief : {brief}

BRAND KIT :
- Couleur primaire  : {ctx.primary_color}
- Couleur accent    : {ctx.accent_color}
- Couleur fond      : {ctx.background_color}
- Couleur texte     : {ctx.text_color}
- Police titres     : {ctx.title_font}
- Police corps      : {ctx.body_font}

TACHE :
Conçois un site vitrine simple et minimaliste pour « {ctx.brand_name} ».
4 à 5 sections maximum. Style epure et professionnel.
Renvoie UNIQUEMENT le JSON impose. Aucun texte autour.
"""
