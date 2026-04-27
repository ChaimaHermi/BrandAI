"""
Phase 3 — Génération du site HTML/Tailwind/JS complet.

Le LLM produit un document HTML autonome (single file) :
- Tailwind via CDN (`https://cdn.tailwindcss.com`) avec config inline pour les couleurs de marque
- Google Fonts en <link> selon les fonts brand kit
- Sections décrites en Phase 2
- Animations CSS / scroll-driven via IntersectionObserver
- SEO basique (meta description, og:tags, title)
- Responsive mobile / desktop

Sortie : un seul document HTML brut. Pas de JSON, pas de markdown.
"""

from __future__ import annotations

import json
from typing import Any

from tools.website_builder.brand_context_fetch import BrandContext


WEBSITE_GENERATION_SYSTEM = """Tu es un Senior Front-End Engineer + Web Designer. Tu génères un site vitrine PRODUCTION-READY en un seul fichier HTML.

CONTRAT DE SORTIE — STRICT :
- Tu renvoies UNIQUEMENT un document HTML complet, commençant par `<!DOCTYPE html>` et finissant par `</html>`.
- Aucun texte avant ou après le HTML.
- Aucune balise markdown (pas de ```html ... ```).
- Aucune explication, aucun commentaire conversationnel.

EXIGENCES TECHNIQUES :
1. Tailwind via CDN : `<script src="https://cdn.tailwindcss.com"></script>` dans le <head>.
2. Configurer Tailwind inline dans <head> via `tailwind.config = { theme: { extend: { colors: {...}, fontFamily: {...} } } }` AVANT le rendu (script avant <body>) en utilisant exactement les couleurs/fonts du brand kit fourni.
3. Importer les Google Fonts demandées via <link> dans <head>.
4. Le HTML doit contenir toutes les sections décrites dans la description Phase 2 (header, hero, ..., footer), DANS L'ORDRE.
5. Contenu textuel COMPLET et plausible pour la marque (pas de lorem ipsum). Utiliser le slogan et le brief comme matière première.
6. Animations :
   - Mettre en place un IntersectionObserver inline pour révéler les sections au scroll (classe .reveal qui passe à .is-visible).
   - Au moins 2 animations CSS keyframes (fade-up, scale-in, etc.).
   - Hover states soignés sur boutons et cartes.
   - Si la description mentionne des compteurs/stats, animer les nombres au scroll en JS pur.
7. Responsive : layout mobile-first, breakpoints `md:` et `lg:` Tailwind. Menu burger mobile fonctionnel (toggle JS) si header présent.
8. SEO basique :
   - <title>{brand_name} — {slogan ou tagline}</title>
   - <meta name="description" content="...">
   - <meta property="og:title">, og:description, og:type=website
   - lang="fr" ou "en" selon la langue du brand kit
9. Logo :
   - Si une logo_url HTTPS est fournie : <img src="..." alt="{brand_name}" class="..."> avec fallback (textuel si erreur).
   - Sinon : composer un wordmark stylé avec la font de titre + couleur primaire.
10. Couleurs : utiliser EXCLUSIVEMENT les couleurs du brand kit (par référence Tailwind après config, ex `bg-brand-primary`, ou via classes arbitraires `bg-[#xxxxxx]`).
11. Accessibilité minimale : alt sur les images, aria-label sur les boutons d'icône, contrastes texte/fond cohérents.
12. Aucune dépendance externe en plus de Tailwind CDN et Google Fonts. Pas de framework JS. Pas d'images binaires en base64.

QUALITÉ VISUELLE ATTENDUE :
- Niveau Awwwards : composition, espace blanc, hiérarchie typographique forte, micro-interactions.
- Hero plein écran (h-screen min-h-[600px]) avec accroche claire + CTA principal.
- Footer avec mentions, liens, accroche finale.
- Au moins 3 sections distinctes entre hero et footer.
- Pas de design plat / template basique.

RAPPEL FINAL :
- N'écris RIEN d'autre que le document HTML (de `<!DOCTYPE html>` à `</html>` inclus).
- Si une exigence est impossible, débrouille-toi quand même : ne renvoie jamais d'erreur ou de message conversationnel.
"""


def _description_for_prompt(description: dict[str, Any]) -> str:
    """Compacte la description Phase 2 pour le prompt sans la dénaturer."""
    return json.dumps(description or {}, ensure_ascii=False, indent=2)


def build_website_generation_user_prompt(
    ctx: BrandContext,
    description: dict[str, Any],
) -> str:
    # IMPORTANT:
    # - On N'INJECTE PAS de data URL base64 dans le prompt (explose la taille/latence).
    # - Si logo URL HTTP(S), on la passe.
    # - Sinon, on signale la présence logo sans payload brut et on demande un placeholder/wordmark.
    raw_logo_url = (ctx.logo_url or "").strip()
    if raw_logo_url.startswith(("http://", "https://")):
        logo_line = raw_logo_url
    elif raw_logo_url.startswith("data:"):
        logo_line = "(logo disponible en base, ne pas injecter inline ; utiliser placeholder/wordmark)"
    else:
        logo_line = "(aucun logo URL — composer un wordmark stylé)"
    slogan_line = ctx.slogan or "(aucun slogan)"

    return f"""LANGUE DU SITE : {ctx.language}

BRAND KIT À UTILISER STRICTEMENT (Tailwind config + classes inline) :
- Couleur primaire    : {ctx.primary_color}   (clé Tailwind: brand-primary)
- Couleur secondaire  : {ctx.secondary_color} (clé Tailwind: brand-secondary)
- Couleur accent      : {ctx.accent_color}    (clé Tailwind: brand-accent)
- Couleur fond        : {ctx.background_color} (clé Tailwind: brand-bg)
- Couleur texte       : {ctx.text_color}      (clé Tailwind: brand-text)
- Police titres       : {ctx.title_font}      (clé Tailwind fontFamily: title)
- Police corps        : {ctx.body_font}       (clé Tailwind fontFamily: body)

INFOS MARQUE :
- Nom de marque : {ctx.brand_name}
- Slogan        : {slogan_line}
- Logo URL      : {logo_line}
- Secteur       : {ctx.sector or '(non précisé)'}
- Public cible  : {ctx.target_audience or '(non précisé)'}
- Pitch         : {ctx.short_pitch or '(non fourni)'}
- Brief         : {ctx.description_brief or '(non fourni)'}
- Direction visuelle : {ctx.visual_style}

DESCRIPTION DU SITE (Phase 2 — à respecter intégralement, sections dans l'ordre indiqué) :
{_description_for_prompt(description)}

CONSIGNE :
Construis MAINTENANT le site complet en un seul document HTML autonome conforme aux règles système. Ne renvoie rien d'autre que le HTML.
"""
