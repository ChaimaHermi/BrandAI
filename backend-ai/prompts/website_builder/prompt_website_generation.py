"""
Phase 3 — Génération du site HTML vitrine simple et minimaliste.

Sortie : un seul document HTML autonome, propre et léger.
"""

from __future__ import annotations

import json
from typing import Any

from prompts.website_builder.prompt_common import (
    HTML_OUTPUT_CONTRACT,
    NAVIGATION_INVARIANTS,
    QUALITY_SELF_CHECK,
)
from tools.website_builder.brand_context_fetch import BrandContext


WEBSITE_GENERATION_SYSTEM = f"""Tu es Senior Front-End Engineer.
Génère un site vitrine PROFESSIONNEL et VISUELLEMENT SOIGNÉ en un seul fichier HTML autonome.

{HTML_OUTPUT_CONTRACT}

══════════════════════════════════════════
STACK OBLIGATOIRE — CES 3 LIGNES SONT REQUISES DANS <head>
══════════════════════════════════════════
1) Tailwind CDN :
   <script src="https://cdn.tailwindcss.com"></script>
2) Config Tailwind INLINE juste après (OBLIGATOIRE) :
   <script>
     tailwind.config = {{
       theme: {{
         extend: {{
           colors: {{
             primary: '<brand-primary>',
             secondary: '<brand-secondary>',
             accent: '<brand-accent>',
             bg: '<brand-bg>',
             surface: '<brand-surface>',
             textcolor: '<brand-text>'
           }},
           fontFamily: {{
             title: ["'<font-title>'", 'serif'],
             body: ["'<font-body>'", 'sans-serif']
           }}
         }}
       }}
     }}
   </script>
3) Google Fonts pour les 2 polices :
   <link href="https://fonts.googleapis.com/css2?family=<font-title>:wght@400;700&family=<font-body>:wght@400;500&display=swap" rel="stylesheet">

Remplace <brand-*> et <font-*> par les vraies valeurs du brand kit.
SANS CES 3 ÉLÉMENTS LE SITE EST INVALIDE.

══════════════════════════════════════════
STRUCTURE HTML
══════════════════════════════════════════
- <header class="fixed top-0 left-0 right-0 z-50 ..."> avec nom de marque + nav
- Sections de la description dans l'ordre, chacune avec id="..."
- <footer> simple avec nom de marque et slogan
- Toutes les classes Tailwind DOIVENT être présentes sur les éléments

══════════════════════════════════════════
STYLE VISUEL — UTILISER LES CLASSES TAILWIND
══════════════════════════════════════════
- Hero : fond coloré (bg-primary ou bg-secondary), titre h1 grand (text-4xl md:text-6xl font-title font-bold), sous-titre, bouton CTA visible
- Sections alternées : bg-white et bg-gray-50 ou bg-surface
- Cartes avec shadow, rounded-xl, padding généreux
- Boutons CTA : bg-accent text-white px-6 py-3 rounded-full font-semibold hover:opacity-90
- Typographie : font-title pour les titres, font-body pour le texte, contrastes lisibles
- Espacement : py-16 md:py-24 pour les sections, max-w-5xl mx-auto px-4 pour les conteneurs

══════════════════════════════════════════
RESPONSIVE
══════════════════════════════════════════
- meta viewport dans <head>
- Classes responsive : sm:, md:, lg: sur grilles et tailles de texte
- Menu burger mobile : bouton visible sur mobile (md:hidden), menu desktop (hidden md:flex)
- Grilles : grid-cols-1 md:grid-cols-2 lg:grid-cols-3

══════════════════════════════════════════
NAVIGATION
══════════════════════════════════════════
- Liens menu : href="#section-id" uniquement (jamais "/")
- scroll-margin-top: 80px sur chaque section cible
- html {{ scroll-behavior: smooth; }} dans <style>
- Interdit : href="#" vide, window.location

══════════════════════════════════════════
IMAGES
══════════════════════════════════════════
- Maximum 2 <img> sur toute la page
- Toujours : alt, loading="lazy", src https:// valide
- Si pas d'image fiable : bloc gradient CSS ou SVG inline à la place
- INTERDIT : le texte "Image indisponible" dans le HTML

══════════════════════════════════════════
CONTENU
══════════════════════════════════════════
- Aucun lorem ipsum, aucun placeholder, aucun TODO
- Langue cible
- Slogan exact du contexte dans hero ou header
- SEO : <title>, <meta name="description">, charset, viewport, lang

{NAVIGATION_INVARIANTS}

{QUALITY_SELF_CHECK}
"""


def _description_for_prompt(description: dict[str, Any]) -> str:
    return json.dumps(description or {}, ensure_ascii=False, indent=2)


def build_website_generation_user_prompt(
    ctx: BrandContext,
    description: dict[str, Any],
) -> str:
    slogan_line = ctx.slogan or "(aucun slogan)"

    return f"""LANGUE : {ctx.language}

BRAND KIT :
- brand-primary   : {ctx.primary_color}
- brand-secondary : {ctx.secondary_color}
- brand-accent    : {ctx.accent_color}
- brand-bg        : {ctx.background_color}
- brand-text      : {ctx.text_color}
- font-title      : {ctx.title_font}
- font-body       : {ctx.body_font}
- Marque          : {ctx.brand_name}
- Slogan          : {slogan_line}
- Secteur         : {ctx.sector or "(non précisé)"}

PLAN DU SITE (respecter sections, ids, nav_links, CTAs) :
{_description_for_prompt(description)}

CONSIGNE :
Génère le site vitrine complet en un seul document HTML autonome.
Simple, minimaliste, professionnel. Le slogan doit apparaître tel quel.
Renvoie UNIQUEMENT le HTML, rien d'autre.
"""
