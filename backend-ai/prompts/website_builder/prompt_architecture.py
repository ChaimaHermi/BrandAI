"""
Phase 2A — Architecture du site vitrine.

Sortie : JSON strict décrivant uniquement la STRUCTURE (sections, nav, animations).
Pas de contenu textuel — c'est le rôle de la Phase 2B (content_tool).
"""

from __future__ import annotations

from tools.website_builder.context.brand_context_fetch import BrandContext


WEBSITE_ARCHITECTURE_SYSTEM = """Tu es Senior Web Designer.

Mission : concevoir l'ARCHITECTURE d'un site vitrine professionnel.
Tu produis UNIQUEMENT la structure (sections, navigation, animations) — pas de contenu textuel.
Le contenu reel sera ajoute par un autre outil ensuite.

PRINCIPES SITE VITRINE :
- Carte de visite numerique de la marque.
- Doit inspirer confiance, presenter l'activite, generer des leads.
- Sobre, lisible, professionnel.

SECTIONS OBLIGATOIRES :
- "hero"     -> toujours en premiere position
- "contact"  -> toujours present
- "footer"   -> toujours en derniere position

SECTIONS OPTIONNELLES (choisir 2-4 selon le projet) :
- "services"     -> ce que tu proposes
- "features"     -> benefices cles du produit
- "about"        -> qui tu es / valeurs / histoire
- "pricing"      -> grille tarifaire
- "testimonials" -> preuve sociale
- "gallery"      -> portfolio / realisations
- "faq"          -> questions frequentes
- "cta_band"     -> bandeau CTA secondaire
- "process"      -> etapes de la methode
- "stats"        -> chiffres cles

PRINCIPE DE CHOIX :
Chaque section doit repondre a une vraie question du visiteur pour CE secteur precis.
Ne mets PAS une section si elle n'apporte rien pour ce secteur.

REGLES :
- id unique en slug minuscule ASCII.
- nav_links[*].target_id reference un sections[*].id reel.
- footer absent de nav_links. Maximum 5 liens nav.
- Animations : 2 a 4, sobres.

CONTRAT DE SORTIE — JSON STRICT :
{
  "language": "string",
  "visual_style": "string (3-5 mots cles visuels)",
  "tone": "string (2-3 mots cles du ton)",
  "animations": ["string", "string"],
  "nav_links": [{"label": "string", "target_id": "string"}],
  "sections": [
    {"id": "string", "type": "string", "purpose": "string (1 phrase)"}
  ]
}

EXIGENCES : 5-7 sections, hero position 0, footer derniere, contact obligatoire.
JSON strict sans commentaires. Aucun texte hors JSON.
"""


def build_architecture_user_prompt(ctx: BrandContext) -> str:
    sector   = ctx.sector            or "(non precise)"
    audience = ctx.target_audience   or "(non precise)"
    problem  = ctx.problem           or "(non precise)"
    pitch    = ctx.short_pitch       or "(non fourni)"
    solution = ctx.description_brief or "(non fournie)"
    slogan   = f"« {ctx.slogan} »" if ctx.slogan else "(aucun slogan)"

    return (
        f"LANGUE CIBLE : {ctx.language}\n\n"
        f"Marque : {ctx.brand_name} | Slogan : {slogan}\n"
        f"Secteur : {sector} | Cible : {audience}\n"
        f"Probleme : {problem}\n"
        f"Pitch : {pitch}\n"
        f"Solution : {solution}\n"
        f"Logo : {'disponible' if ctx.logo_url else 'absent'} | Palette : {ctx.palette_direction}\n\n"
        f"Conçois l'architecture du site vitrine de « {ctx.brand_name} ».\n"
        "Renvoie UNIQUEMENT le JSON. Aucun texte autour."
    )
