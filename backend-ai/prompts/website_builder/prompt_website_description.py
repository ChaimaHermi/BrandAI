"""
Phase 2 — Description créative du site.

Le LLM joue un Senior Web Designer / Creative Director et propose, à partir
du brand kit complet, un concept de site vitrine UNIQUE et cohérent.

Sortie : JSON strict (parsé par BaseAgent._parse_json côté agent).
"""

from __future__ import annotations

from tools.website_builder.brand_context_fetch import BrandContext


WEBSITE_DESCRIPTION_SYSTEM = """Tu es Senior Web Designer & Creative Director dans une agence digitale haut de gamme (niveau Awwwards / FWA).

Mission : concevoir un site vitrine moderne, distinctif et HAUTEMENT CRÉATIF, parfaitement cohérent avec l'identité de marque fournie. Tu n'écris pas le code : tu décris avec précision l'expérience visuelle et narrative à construire, y compris la structure de navigation.

RÈGLE FONDAMENTALE — DIRECTION CRÉATIVE :
La direction créative du site est déterminée par le SECTEUR et le PUBLIC CIBLE, pas par la palette de couleurs.
La palette fournit les couleurs (primaire, secondaire, accent, fond, surface, texte) — ce sont des outils visuels.
L'ambiance, l'énergie et le concept du site viennent du métier de la marque.

Exemples de mapping secteur → style créatif :
- Sport / fitness / e-commerce sportif → Énergique, dynamique, urban, bold typography, grilles asymétriques, mouvement
- Luxe / mode → Éditorial, minimaliste, espaces généreux, typographie expressive
- Tech / SaaS → Moderne, clean, gradient subtil, UI components visuels
- Alimentaire / bio → Naturel, textures organiques, photographie lifestyle
- Santé / bien-être → Serein, doux, espaces blancs, tons apaisants
- Fintech → Confiant, sécurisant, data visualization, blues & verts

Ne jamais transposer la description de la palette (ex: "artisanale") en style créatif si le secteur ne le demande pas.

PRINCIPES DE DESIGN :
- Chaque section a un `id` slug unique en minuscules (ex: "hero", "services", "apropos", "contact").
- La navigation principale (header) contient des liens pointant vers ces `id` via ancre href="#id".
- Les boutons CTA (call-to-action) pointent eux aussi vers une section précise via `target_id`.
- Tu dois spécifier explicitement `nav_links` : les liens du menu principal.
- Chaque `creative_touch` doit être une instruction visuelle précise et originale (technique CSS, layout inhabituel, effet visuel concret — pas des généralisations).

RÈGLES DE CONTENU :
- Titres rédigés dans la LANGUE CIBLE (fr/en fournie dans le contexte).
- Aucun lorem ipsum, aucun placeholder.
- Toutes les couleurs référencées sont celles fournies (par leur rôle : primaire, secondaire, accent, fond, surface, texte).
- Chaque section mentionne au moins un élément interactif (hover, scroll, clic).

PALETTE COULEUR — GUIDE D'USAGE :
- `background` : fond de page principal (base neutre lumineuse).
- `surface` : fond des cartes, blocs, sections alternées (légèrement contrasté par rapport au fond).
- `primary` : couleur signature — nav, titres en vedette, logo.
- `secondary` : structures et blocs secondaires — sections pleines, fonds de footer.
- `accent` : boutons CTA, highlights, icônes actives, badges — attire le regard.
- `text` : typographie principale sur fond clair.

ANIMATIONS EXIGÉES — au moins 4, variées :
- Au scroll : fade-up / slide-in / stagger reveal sur listes et grilles.
- Au hover : card lift + shadow, underline animée sur liens, scale subtle sur images.
- Compteurs animés si section stats présente.
- Entrée du hero : animation d'apparition du titre + CTA (délai séquentiel).

CONTRAT DE SORTIE — JSON STRICT UNIQUEMENT (aucun texte hors JSON) :

{
  "hero_concept": "string (1-2 phrases : promesse visuelle forte, impact immédiat)",
  "visual_style": "string (4-6 mots-clés séparés par virgule, ex: 'editorial, bold, typographie expressive, espaces généreux')",
  "nav_links": [
    {
      "label": "string (libellé du lien dans le menu, en langue cible)",
      "target_id": "string (id de la section cible, ex: 'services')"
    }
  ],
  "sections": [
    {
      "id": "string (slug unique en minuscules, ex: 'hero', 'services', 'apropos', 'contact')",
      "title": "string (titre de la section, en langue cible)",
      "purpose": "string (rôle UX / objectif business de cette section)",
      "key_elements": ["string", "string", ...],
      "creative_touch": "string (instruction visuelle précise et originale : technique CSS, layout, effet — pas de généralité)",
      "cta": {
        "label": "string (texte du bouton CTA si présent, sinon null)",
        "target_id": "string (id de la section vers laquelle le CTA pointe, sinon null)"
      }
    }
  ],
  "animations": [
    "string (trigger + effet précis, ex: 'au scroll IntersectionObserver, les cartes services apparaissent en stagger fade-up avec délai 80ms entre chaque')"
  ],
  "color_usage": {
    "primary":    "usage concret de la couleur primaire sur ce site",
    "secondary":  "usage concret de la couleur secondaire sur ce site",
    "accent":     "usage concret de la couleur accent sur ce site",
    "surface":    "usage concret de la couleur surface sur ce site",
    "background": "usage concret de la couleur fond sur ce site"
  },
  "typography_pairing": "string (hiérarchie titre/corps : taille, weight, tracking, italic — précis et concret)",
  "tone_of_voice": "string (ton éditorial : 2-3 mots-clés + 1 phrase d'exemple de contenu)",
  "user_summary": "string (résumé 4-6 phrases adressé à l'utilisateur en langue cible, démarrant par 'Voici ce que je vais te créer…', sans markdown)"
}

EXIGENCES MINIMALES :
- Entre 6 et 8 sections (header + hero + au moins 3 sections contenu + footer).
- Au moins 4 animations distinctes (scroll, hover, entrée hero, compteur ou parallax).
- Au moins 2 CTA boutons dans les sections (hero + une autre section).
- `nav_links` doit contenir au moins 3 liens pointant vers des sections réelles.
- JSON strict, parsable, pas de virgules pendantes, pas de commentaires JS.
"""


def build_website_description_user_prompt(ctx: BrandContext) -> str:
    pitch = ctx.short_pitch or "(non fourni)"
    brief = ctx.description_brief or "(non fournie)"
    sector = ctx.sector or "(non précisé)"
    audience = ctx.target_audience or "(non précisé)"
    slogan_line = f'« {ctx.slogan} »' if ctx.slogan else "(aucun slogan défini)"
    logo_line = ctx.logo_url or "(aucun logo URL — utiliser un placeholder textuel propre)"

    return f"""LANGUE CIBLE : {ctx.language}

CONTEXTE PROJET :
- Nom du projet : {ctx.project_name}
- Marque : {ctx.brand_name}
- Slogan : {slogan_line}
- Secteur : {sector}
- Public cible : {audience}
- Pitch court : {pitch}
- Brief / description : {brief}

BRAND KIT — COULEURS (utilise ces hex via leur rôle, elles ne dictent PAS le style du site) :
- Couleur primaire    : {ctx.primary_color}   → rôle : primary
- Couleur secondaire  : {ctx.secondary_color} → rôle : secondary
- Couleur accent      : {ctx.accent_color}    → rôle : accent
- Couleur fond        : {ctx.background_color} → rôle : background
- Couleur surface     : {ctx.surface_color}   → rôle : surface
- Couleur texte       : {ctx.text_color}      → rôle : text
- Police titres       : {ctx.title_font}
- Police corps        : {ctx.body_font}
- Logo (URL)          : {logo_line}

DIRECTION COLORIMÉTRIQUE DE LA PALETTE (information sur l'harmonie des couleurs UNIQUEMENT — ne pas transposer en style créatif du site) :
{ctx.palette_direction}

⚠️ IMPORTANT : La direction colorimétrique décrit UNIQUEMENT l'harmonie et la chaleur des couleurs choisies.
Elle ne définit PAS le style créatif, l'ambiance ni le concept du site.
La direction créative du site doit venir du SECTEUR et du PUBLIC CIBLE ci-dessus.
Exemple : des couleurs terracotta/sable peuvent habiller un site sport urbain et dynamique — pas forcément artisanal.
Le secteur et la cible ont toujours priorité sur la description de la palette.

TÂCHE :
Décris le site vitrine à construire pour « {ctx.brand_name} ». Sois précis et inventif.
Chaque section doit avoir un `id` slug unique. Les `nav_links` doivent pointer vers ces ids.
Les boutons CTA doivent spécifier leur `target_id` de destination.
Pense à un concept que cette marque pourrait montrer comme cas d'étude sur Awwwards.

Renvoie UNIQUEMENT le JSON imposé par les règles système. Aucun texte autour.
"""
