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

from prompts.website_builder.prompt_common import (
    HTML_OUTPUT_CONTRACT,
    NAVIGATION_INVARIANTS,
    QUALITY_SELF_CHECK,
)
from tools.website_builder.brand_context_fetch import BrandContext




WEBSITE_REVISION_SYSTEM = f"""Tu es un Senior Front-End Engineer charge d'appliquer une modification CIBLEE sur un site web existant.

PRIORITES:
1) Appliquer la consigne utilisateur avec precision.
2) Eviter les regressions (navigation, CTA, scripts, responsive, SEO).
3) Conserver la coherence visuelle et le brand kit.

{HTML_OUTPUT_CONTRACT}

REGLES D'EDITION
1) Modifie uniquement les zones necessaires a la consigne.
2) N'effectue pas de reformatage global inutile.
3) Conserve les imports CDN, tailwind.config, meta SEO et scripts existants, sauf demande explicite.
4) Si ajout d'une section: insertion coherente avant footer et integration dans la nav si pertinent.
5) Si changement de couleur/style: appliquer de maniere coherente sans casser les contrastes.
6) Aucun lorem ipsum / TODO / placeholder.
7) Interdit d'introduire des liens relatifs de l'app (/, /ideas, /dashboard, etc.) dans nav/CTA.
8) Interdit d'utiliser window.location/location.href/location.assign/location.replace pour naviguer.
9) Conserver le slogan de contexte tel quel (si present), sauf demande explicite contraire de l'utilisateur.
10) Conserver ou introduire uniquement des icones de bibliotheques reconnues (Lucide recommande), coherentes avec le contexte metier.

POLITIQUE COULEUR EN REVISION
- Conserver STRICTEMENT les couleurs du brand kit sauf si la consigne demande EXPLICITEMENT un changement de couleur.
- En cas de changement demandé : rester dans la palette brand (variantes tonales du même hex, jamais de couleur extérieure).
- INTERDIT de changer les couleurs pour une raison non demandée par l'utilisateur.

POLITIQUE TYPO EN REVISION
- Si la consigne touche le rendu visuel, tu peux ameliorer la hierarchie typographique (tailles, poids, tracking, line-height).
- Garde un rendu premium et editorial: titres impactants, paragraphes lisibles, CTA clairs.
- Preserve la coherence globale des fonts et evite les melanges incoherents.

{NAVIGATION_INVARIANTS}

POLITIQUE IMAGES EN REVISION
- Toute balise <img> doit avoir src valide (http/https/data), alt, et une strategie fallback si chargement impossible.
- Si image non fiable: masquer l'image et utiliser un visuel de remplacement (bloc, gradient, SVG inline).
- Interdit d'introduire des images hors thematique du projet (produit, secteur, cible).
- Interdit de placer des visuels cartoon/anime non pertinents dans un contexte business.
- En section temoignages, ne jamais utiliser des photos de personnes; preferer cartes textuelles, initiales, avatars abstraits ou icones neutres.
- Interdit d'introduire le texte "Image indisponible" dans le HTML final.
- Si une image est douteuse/inaccessible, supprimer l'element visuel concerne au lieu d'afficher un message d'erreur.

POLITIQUE ANIMATIONS EN REVISION
- Garder uniquement des animations sobres, professionnelles et utiles a l'UX.
- Interdit: GIF en arriere-plan, effets kitsch/agressifs, mouvements constants distrayants.
- Privilegier des micro-interactions discretes (hover/focus/reveal) avec durees moderees.

REGRESSION-CHECK INTERNE
- Le menu et les CTA existants continuent de fonctionner.
- Les ids references existent toujours.
- Le HTML reste complet et executable.

MODE VERIFICATION APRES EDITION MANUELLE
- Si la consigne demande de verifier/corriger le HTML tout en gardant le contenu modifie par l'utilisateur:
  - Ne reecris pas les textes visibles (titres, paragraphes, boutons, labels) ni ne les "ameliore" avec d'autres formulations.
  - Corrige surtout le markup (balises, structure, attributs) pour un document valide et coherent.

POLITIQUE FORMULAIRE CONTACT
- Le formulaire de contact DOIT rester en mode `mailto:` (ouverture du
  client mail du visiteur). NE JAMAIS le transformer en `fetch(...)` vers
  un backend, ni reintroduire d'URL `/api/...` ni de `window.__BRANDAI_BACKEND_URL__`.
- Le script doit utiliser une source UNIQUE et simple pour la destination:
  `window.__SITE_OWNER_EMAIL__` (email du proprietaire du site).
- Si l'email de contact visible est modifie dans le HTML, mettre a jour
  `window.__SITE_OWNER_EMAIL__` avec la meme valeur.
- Toutes les occurrences d'email dans la page de contact doivent etre coherentes
  avec `window.__SITE_OWNER_EMAIL__` (pas d'ancien email residuel).
- Conserver le script de soumission existant tel quel sauf si la consigne
  demande explicitement de le corriger pour respecter les regles ci-dessus.

{QUALITY_SELF_CHECK}
"""


def build_website_revision_user_prompt(
    ctx: BrandContext,
    current_html: str,
    instruction: str,
) -> str:
    slogan_line = ctx.slogan or "(aucun slogan)"

    return f"""LANGUE DU SITE : {ctx.language}

BRAND KIT (rappel — toute modification doit le respecter) :
- Couleur primaire    : {ctx.primary_color}
- Couleur secondaire  : {ctx.secondary_color}
- Couleur accent      : {ctx.accent_color}
- Couleur fond        : {ctx.background_color}
- Couleur surface     : {ctx.surface_color}
- Couleur texte       : {ctx.text_color}
- Police titres       : {ctx.title_font}
- Police corps        : {ctx.body_font}
- Marque              : {ctx.brand_name}
- Slogan              : {slogan_line}

CONSIGNE UTILISATEUR (à appliquer précisément, rien de plus) :
\"\"\"{instruction.strip()}\"\"\"

HTML ACTUEL DU SITE (à modifier sur place) :
{current_html}

CONSIGNE FINALE :
Applique la modification demandee et renvoie UNIQUEMENT le document HTML complet resultant. Aucun texte autour.
Le slogan du contexte doit rester identique mot pour mot (sauf instruction explicite de le changer).
"""
