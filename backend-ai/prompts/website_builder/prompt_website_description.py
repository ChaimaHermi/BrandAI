"""
Phase 2 — Description créative du site.

Le LLM joue un Senior Web Designer / Creative Director et propose, à partir
du brand kit complet, un concept de site vitrine UNIQUE et cohérent.

Sortie : JSON strict (parsé par BaseAgent._parse_json côté agent).
"""

from __future__ import annotations

from tools.website_builder.brand_context_fetch import BrandContext


def _safe_logo_line(raw_logo_url: str | None) -> str:
    raw = (raw_logo_url or "").strip()
    if raw.startswith(("http://", "https://")):
        return raw
    if raw.startswith("data:"):
        return "(logo inline base64 masque pour prompt propre)"
    return "(aucun logo URL — utiliser un placeholder textuel propre)"


WEBSITE_DESCRIPTION_SYSTEM = """Tu es Senior Web Designer & Creative Director.

Mission: produire un PLAN de site vitrine (pas le code), moderne et coherent.
Le plan doit etre directement exploitable pour la generation HTML.

PRIORITES
1) Coherence business (secteur + cible).
2) Coherence structurelle (ids, nav_links, cta.target_id).
3) Precision visuelle exploitable (pas de generalites vagues).
4) Sortie JSON strictement valide.

REGLE FONDAMENTALE
La direction creative vient du secteur et du public cible.
La palette fournie sert d'inspiration (humeur, temperature, energie), pas de contrainte stricte 1:1.
Tu peux proposer des nuances et degradés harmonieux issus de cette inspiration pour obtenir un meilleur rendu.

REGLES DE STRUCTURE (NON NEGOCIABLES)
- Chaque section a un `id` unique (slug minuscule, ascii, sans espaces).
- `nav_links[*].target_id` reference un `sections[*].id` reel.
- `sections[*].cta.target_id` (si non null) reference un `sections[*].id` reel.
- Chaque section doit avoir un role UX/business clair.
- `creative_touch` doit etre concret (layout, effet, motif), jamais abstrait.

REGLES DE CONTENU
- Langue cible obligatoire.
- Aucun lorem ipsum / placeholder / TODO.
- Les choix couleurs doivent rester alignes avec l'esprit de la palette choisie, sans obligation d'utiliser strictement chaque hex.
- Au moins une interaction mentionnee par section (hover, scroll, click, reveal).
- La proposition typographique doit viser un rendu premium: hierarchy claire, titres memorables, texte lisible, rythme editorial.
- Les animations doivent rester sobres, professionnelles et utiles a l'UX (interdit: GIF decoratif, effets cartoon, blink, animations agressives, loops distrayantes).
- Chaque animation doit etre simple, fluide, discrete et pertinente pour un site business moderne.
- Interdit d'ajouter des visuels hors sujet: toute image/illustration doit etre directement liee au secteur, au produit et a l'idee du projet.
- Interdit strict: images de style dessin anime pour des contextes business non ludiques.
- Si la pertinence d'une image est incertaine, ne pas proposer d'image et preferer formes, gradients, patterns abstraits ou icones neutres.
- Dans une section temoignages, ne jamais imposer de photo de personne/retrait portrait; utiliser avatars abstraits, initiales, ou cartes textuelles sans visage.
- Objectif global: sections bien structurees, style premium, rendu professionnel.
- Les icones doivent provenir d'une bibliotheque reconnue (ex: Lucide Icons, Heroicons, Tabler). Eviter les icones improvisees incoherentes.
- Prevoir des usages d'icones coherents (features, steps, CTA secondaires) pour renforcer la clarte visuelle.

CONTRAT DE SORTIE — JSON STRICT UNIQUEMENT :

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
    "dominant":      "usage de la famille de couleurs dominante (inspiree de la palette)",
    "supporting":    "usage des couleurs de soutien (nuances/teintes intermediaires)",
    "highlight":     "usage des couleurs d'accent et points d'attention",
    "surfaces":      "strategie couleur pour sections/cartes/fonds alternes",
    "gradients_fx":  "description des degradés/overlays/variations tonales utilises"
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
- Les `nav_links` doivent etre coherents avec la structure reelle du site et orienter vers des sections business utiles.

AUTO-VERIFICATION INTERNE AVANT REPONSE
- Tous les target_id references existent vraiment dans sections.id.
- Tous les ids sont uniques et en slug minuscule.
- Le JSON est valide, sans texte autour.
- La typographie proposee est concretement exploitable et visuellement professionnelle.
- Les animations restent sobres/pro et sans effet kitsch.
- Aucun visuel hors thematique, aucune photo de personne en temoignages.
"""


def build_website_description_user_prompt(ctx: BrandContext) -> str:
    pitch = ctx.short_pitch or "(non fourni)"
    brief = ctx.description_brief or "(non fournie)"
    sector = ctx.sector or "(non précisé)"
    audience = ctx.target_audience or "(non précisé)"
    slogan_line = f'« {ctx.slogan} »' if ctx.slogan else "(aucun slogan défini)"
    logo_line = _safe_logo_line(ctx.logo_url)

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

⚠️ IMPORTANT :
- La direction colorimétrique décrit l'ambiance générale (harmonie/chaleur), pas une contrainte stricte.
- Tu peux enrichir la palette avec des teintes intermediaires, des degradés et des variations tonales.
- Le resultat final doit rester coherent avec l'identite percue de la palette choisie.
- Le secteur et la cible ont toujours priorite sur la seule couleur.

TÂCHE :
Décris le site vitrine à construire pour « {ctx.brand_name} ». Sois précis et inventif.
Chaque section doit avoir un `id` slug unique. Les `nav_links` doivent pointer vers ces ids.
Les boutons CTA doivent spécifier leur `target_id` de destination.
Pense à un concept que cette marque pourrait montrer comme cas d'étude sur Awwwards.

Renvoie UNIQUEMENT le JSON imposé par les règles système. Aucun texte autour.
"""
