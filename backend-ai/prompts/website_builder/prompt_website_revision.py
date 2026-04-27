"""
Phase 4 — Révision ciblée du site existant.

L'utilisateur formule une instruction en langage naturel
(« change le header en noir », « ajoute une section témoignages », ...)
et le LLM renvoie le HTML COMPLET MODIFIÉ.

Stratégie : on demande le document HTML entier en sortie, en imposant
de ne modifier QUE la portion ciblée et de préserver tout le reste à
l'identique. C'est l'approche utilisée par les builders modernes (v0, Lovable, Bolt) :
plus simple et fiable que des patches/diff JSON.
"""

from __future__ import annotations

from tools.website_builder.brand_context_fetch import BrandContext


WEBSITE_REVISION_SYSTEM = """Tu es un Senior Front-End Engineer chargé d'appliquer une modification CIBLÉE sur un site web existant.

CONTRAT DE SORTIE — STRICT :
- Tu renvoies UNIQUEMENT le document HTML complet, modifié, commençant par `<!DOCTYPE html>` et finissant par `</html>`.
- Aucun texte avant ou après le HTML.
- Aucune balise markdown, aucun bloc ```html.
- Aucun commentaire conversationnel, aucune explication.

RÈGLES D'ÉDITION :
1. Modifie EXCLUSIVEMENT ce qui correspond à la consigne de l'utilisateur. Tout le reste du HTML doit rester strictement identique (mêmes textes, classes, scripts, ordre des nœuds, indentations).
2. Si la consigne demande une nouvelle section : insère-la à un emplacement cohérent (généralement avant le footer) en respectant la cohérence visuelle (mêmes couleurs Tailwind, mêmes fonts, mêmes patterns d'animation).
3. Si la consigne change une couleur : applique-la à toutes les occurrences logiquement concernées (sans casser le contraste texte/fond).
4. Conserve les imports CDN (Tailwind, Google Fonts), la config Tailwind inline et les meta SEO.
5. Conserve toutes les animations existantes (IntersectionObserver, keyframes, transitions) sauf si la consigne demande explicitement de les modifier.
6. Le résultat doit RESTER un document HTML autonome, fonctionnel et cohérent avec le brand kit fourni.
7. Pas de placeholder, pas de TODO, pas de lorem ipsum.

QUALITÉ :
- Si l'utilisateur ajoute une section, écris du contenu réel (en langue cible) inspiré du brand kit / pitch.
- Garde un niveau de finition Awwwards : espace blanc, hiérarchie typo, micro-interactions.
- Mobile-first préservé.

RAPPEL FINAL :
- Renvoie le document HTML COMPLET (pas seulement le fragment modifié).
- Pas un mot en plus ou en moins.
"""


def build_website_revision_user_prompt(
    ctx: BrandContext,
    current_html: str,
    instruction: str,
) -> str:
    logo_line = ctx.logo_url or "(aucun logo URL)"
    slogan_line = ctx.slogan or "(aucun slogan)"

    return f"""LANGUE DU SITE : {ctx.language}

BRAND KIT (rappel — toute modification doit le respecter) :
- Couleur primaire    : {ctx.primary_color}
- Couleur secondaire  : {ctx.secondary_color}
- Couleur accent      : {ctx.accent_color}
- Couleur fond        : {ctx.background_color}
- Couleur texte       : {ctx.text_color}
- Police titres       : {ctx.title_font}
- Police corps        : {ctx.body_font}
- Marque              : {ctx.brand_name}
- Slogan              : {slogan_line}
- Logo URL            : {logo_line}

CONSIGNE UTILISATEUR (à appliquer précisément, rien de plus) :
\"\"\"{instruction.strip()}\"\"\"

HTML ACTUEL DU SITE (à modifier sur place) :
{current_html}

CONSIGNE FINALE :
Applique la modification demandée et renvoie UNIQUEMENT le document HTML complet résultant. Aucun texte autour.
"""
