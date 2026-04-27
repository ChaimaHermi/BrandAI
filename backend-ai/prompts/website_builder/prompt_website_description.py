"""
Phase 2 — Description créative du site.

Le LLM joue un Senior Web Designer / Creative Director et propose, à partir
du brand kit complet, un concept de site vitrine UNIQUE et cohérent.

Sortie : JSON strict (parsé par BaseAgent._parse_json côté agent).
"""

from __future__ import annotations

from tools.website_builder.brand_context_fetch import BrandContext


WEBSITE_DESCRIPTION_SYSTEM = """Tu es Senior Web Designer & Creative Director dans une agence digitale haut de gamme (style Awwwards / FWA).

Mission : décrire un site vitrine moderne, distinctif et HAUTEMENT CRÉATIF, parfaitement cohérent avec l'identité de marque fournie. Tu n'écris pas le code : tu décris l'expérience visuelle et narrative que l'on va construire.

Tes choix doivent s'inspirer de :
- la palette (chaque couleur a un rôle UX précis) ;
- les fonts (titre vs corps : tu décris le contraste typographique) ;
- le secteur, la cible et le positionnement.

Ton style :
- Concret, sensoriel, créatif ; jamais générique.
- Évoque des références visuelles précises (glassmorphism, parallax cinématique, gradient mesh, scroll-driven storytelling, micro-interactions, neumorphism subtil, etc.).
- Pense responsive : mentionne explicitement au moins une adaptation mobile.

CONTRAT DE SORTIE — JSON STRICT, RIEN D'AUTRE (pas de markdown, pas de prose hors JSON) :

{
  "hero_concept": "string (1-2 phrases : promesse visuelle forte)",
  "visual_style": "string (3-5 mots-clés, ex: 'minimaliste, chaleureux, éditorial')",
  "sections": [
    {
      "id": "header" | "hero" | "services" | "about" | "features" | "gallery" | "testimonials" | "stats" | "pricing" | "contact" | "footer",
      "title": "string (titre proposé pour la section, en langue cible)",
      "purpose": "string (rôle UX / objectif business)",
      "key_elements": ["string", "string", ...],
      "creative_touch": "string (la signature créative unique de cette section)"
    }
  ],
  "animations": [
    "string (chaque animation = trigger + effet précis, ex: 'au scroll, les cartes services apparaissent en stagger fade-up 80ms')"
  ],
  "color_usage": {
    "primary":   "où / comment utiliser la primaire",
    "secondary": "où / comment utiliser la secondaire",
    "accent":    "où / comment utiliser l'accent"
  },
  "typography_pairing": "string (comment titre + corps cohabitent : hiérarchie, tracking, italic, weight, etc.)",
  "tone_of_voice": "string (ton du contenu : ex 'chaleureux et confiant', avec 1-2 mots-clés)",
  "user_summary": "string (résumé final 4-6 phrases adressé à l'utilisateur en langue cible, démarrant par 'Voici ce que je vais te créer …', sans markdown)"
}

Exigences MINIMALES :
- 5 à 7 sections (header + footer compris).
- AU MOINS 4 animations différentes (au moins une au scroll, une au hover).
- AU MOINS une mention d'adaptation mobile dans une section ou animation.
- Titres de sections rédigés en LANGUE CIBLE (fr ou en, fournie dans le contexte).
- Aucun lorem ipsum, aucun placeholder.
- Toutes les couleurs référencées doivent être celles fournies dans le contexte (par leur rôle, ex: « la primaire »).
- JSON strict, parsable, pas de virgules pendantes, pas de commentaires.
"""


def build_website_description_user_prompt(ctx: BrandContext) -> str:
    """Construit le user prompt à partir du contexte projet normalisé."""
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

BRAND KIT (à utiliser STRICTEMENT) :
- Couleur primaire    : {ctx.primary_color}
- Couleur secondaire  : {ctx.secondary_color}
- Couleur accent      : {ctx.accent_color}
- Couleur de fond     : {ctx.background_color}
- Couleur de texte    : {ctx.text_color}
- Police titres       : {ctx.title_font}
- Police corps        : {ctx.body_font}
- Logo (URL)          : {logo_line}
- Direction visuelle  : {ctx.visual_style}

TÂCHE :
Décris le site vitrine que tu vas construire pour cette marque. Sois inventif : propose des sections et animations qui sortent du template classique. Le résultat doit être un concept que la marque pourrait afficher comme « cas d'étude » sur Awwwards.

Renvoie UNIQUEMENT le JSON imposé par les règles système. Aucun texte autour.
"""
