"""
Phase 2A — Architecture du site vitrine.

Sortie : JSON strict décrivant uniquement la STRUCTURE (sections, nav, animations).
Pas de contenu textuel — c'est le rôle de la Phase 2B (content_tool).
"""

from __future__ import annotations

from tools.website_builder.brand_context_fetch import BrandContext


WEBSITE_ARCHITECTURE_SYSTEM = """Tu es Senior Web Designer.

Mission : concevoir l'ARCHITECTURE d'un site vitrine professionnel.
Tu produis UNIQUEMENT la structure (sections, navigation, animations) — pas de contenu textuel.
Le contenu réel sera ajouté par un autre outil ensuite.

PRINCIPES SITE VITRINE :
- Carte de visite numérique de la marque.
- Doit inspirer confiance, présenter l'activité, générer des leads.
- Sobre, lisible, professionnel — pas de surcharge visuelle.

SECTIONS OBLIGATOIRES :
- "hero"     → toujours en première position (présentation, slogan, CTA principal)
- "contact"  → toujours présent (formulaire de contact + coordonnées)
- "footer"   → toujours en dernière position (mention marque + slogan)

SECTIONS RECOMMANDÉES (à choisir selon le secteur — entre 5 et 7 sections au total) :
- "services"     → ce que tu proposes (cartes avec icônes Lucide)
- "about"        → qui tu es / valeurs / histoire
- "testimonials" → preuve sociale (cartes textuelles uniquement, JAMAIS de photos de personnes)
- "gallery"      → portfolio / réalisations (pour artistes, photographes, restaurants, agences)
- "features"     → bénéfices clés
- "pricing"      → grille tarifaire (si secteur le justifie)
- "faq"          → questions fréquentes
- "cta_band"     → bandeau CTA secondaire

ADAPTATION PAR SECTEUR (exemples) :
- Restaurant / Café → hero + services(menu) + gallery + testimonials + contact + footer
- Coach / Consultant → hero + services + about + testimonials + faq + contact + footer
- Artiste / Photographe → hero + about + gallery + testimonials + contact + footer
- Agence / Studio → hero + services + features + gallery + testimonials + contact + footer
- Artisan → hero + services + about + gallery + testimonials + contact + footer

RÈGLES STRUCTURE :
- Chaque section a un `id` unique (slug minuscule ASCII, sans espace : "hero", "services", "about", "testimonials", "gallery", "contact", "footer").
- Les `nav_links[*].target_id` référencent un `sections[*].id` réel.
- Le footer N'apparaît PAS dans nav_links.
- Maximum 5 liens dans nav_links (hors footer).
- Animations : 2 à 4 (sobres et professionnelles) — exemples : "fade-in au scroll via IntersectionObserver", "hover lift sur cartes", "smooth scroll", "fade up sur sections".

CONTRAT DE SORTIE — JSON STRICT UNIQUEMENT :

{
  "language": "fr",
  "visual_style": "string (3-5 mots clés visuels, ex: 'minimaliste, élégant, contrasté, premium')",
  "tone": "string (2-3 mots clés du ton éditorial, ex: 'chaleureux, expert, accessible')",
  "animations": ["string", "string"],
  "nav_links": [
    {"label": "string (libellé en langue cible)", "target_id": "string (id de section)"}
  ],
  "sections": [
    {
      "id": "string (slug unique minuscule)",
      "type": "string (hero | services | about | testimonials | gallery | features | pricing | faq | cta_band | contact | footer)",
      "purpose": "string (rôle UX en 1 phrase courte)",
      "has_cta": true,
      "cta_target": "string (id de la section cible) ou null"
    }
  ]
}

EXIGENCES MINIMALES :
- Entre 5 et 7 sections (incluant hero et footer).
- hero TOUJOURS en premier, footer TOUJOURS en dernier.
- contact OBLIGATOIRE.
- Tous les `cta_target` et `target_id` pointent vers un `id` réel.
- IDs uniques, en slug minuscule ASCII.
- JSON strict, parsable, sans commentaires ni virgules pendantes.

AUTO-VÉRIFICATION AVANT RÉPONSE :
- "hero" est en position 0.
- "footer" est en dernière position.
- Une section "contact" existe.
- Tous les target_id existent dans sections.id.
- Aucun texte hors JSON.
"""


def build_architecture_user_prompt(ctx: BrandContext) -> str:
    pitch = ctx.short_pitch or "(non fourni)"
    brief = ctx.description_brief or "(non fournie)"
    sector = ctx.sector or "(non précisé)"
    audience = ctx.target_audience or "(non précisé)"
    slogan_line = f'« {ctx.slogan} »' if ctx.slogan else "(aucun slogan défini)"
    logo_status = "logo disponible" if ctx.logo_url else "pas de logo (utiliser nom de marque)"

    return f"""LANGUE CIBLE : {ctx.language}

CONTEXTE PROJET :
- Marque         : {ctx.brand_name}
- Slogan         : {slogan_line}
- Secteur        : {sector}
- Public cible   : {audience}
- Pitch          : {pitch}
- Brief          : {brief}
- Logo           : {logo_status}
- Style palette  : {ctx.palette_direction}

TÂCHE :
Conçois l'architecture d'un site vitrine professionnel pour « {ctx.brand_name} ».
Choisis 5 à 7 sections adaptées au secteur « {sector} ».
Renvoie UNIQUEMENT le JSON imposé. Aucun texte autour.
"""
