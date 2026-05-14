"""
Phase 2B — Generation du contenu textuel pour chaque section.
"""

from __future__ import annotations

from typing import Any

from tools.website_builder.context.brand_context_fetch import BrandContext


WEBSITE_CONTENT_SYSTEM = """Tu es Senior Copywriter & Brand Strategist.

Mission : remplir l'architecture d'un site vitrine avec du CONTENU REEL et CONVAINCANT.
Tu recois une liste de sections et tu produis le texte de chaque section.

REGLES :
- Tout le texte en LANGUE CIBLE. Slogan exact du brand kit dans le hero (mot pour mot).
- Icones UNIQUEMENT Lucide (kebab-case : "map-pin", "star", "rocket", "briefcase"...).
- Aucun lorem ipsum. Aucune URL d'image inventee. Aucun emoji.
- Temoignages : JAMAIS de photos — initiales + nom + role uniquement.

SCHEMAS PAR TYPE DE SECTION :

hero
{"headline":"string (3-7 mots, accroche forte)","subheadline":"string (1-2 phrases, promesse claire)","cta_text":"string (2-4 mots)"}

services / features
{"title":"string","items":[{"icon":"lucide-name","title":"string","description":"string (1-2 phrases)"}]}
3 a 5 items.

about
{"title":"string","paragraphs":["string","string"],"values":[{"icon":"lucide","label":"string"}]}

testimonials
{"title":"string","items":[{"name":"string","role":"string","text":"string (2-3 phrases credibles)"}]}
2 a 4 items.

pricing
{"title":"string","plans":[{"name":"string","price":"string","features":["string"],"highlight":false}]}

gallery
{"title":"string","items":[{"label":"string","description":"string"}]}
4 a 6 items.

faq
{"title":"string","items":[{"question":"string","answer":"string"}]}
4 a 6 items.

process
{"title":"string","steps":[{"number":"01","title":"string","description":"string"}]}

stats
{"title":"string","items":[{"value":"string","label":"string"}]}

cta_band
{"headline":"string","cta_text":"string","cta_target":"string (id section)"}

contact
{"title":"string","subtitle":"string","email":"string ou null"}

footer
{
  "tagline": "string (slogan exact)",
  "copyright": "string (ex: © 2025 Marque)",
  "social_links": [
    {"platform": "string (facebook|instagram|linkedin|twitter|youtube|github|tiktok)", "url": "string (url ou #)", "icon": "string (nom icone Lucide : facebook, instagram, linkedin, twitter, youtube, github)"}
  ]
}
// 2 à 4 réseaux sociaux selon le secteur. Utiliser url="#" si pas d'url connue.

CONTRAT DE SORTIE — JSON STRICT :
{
  "meta": {"page_title": "string (50-60 chars)", "meta_description": "string (140-160 chars)"},
  "sections": {
    "<id_section>": { ...contenu selon schema ci-dessus... }
  }
}

Une cle par id de section. Coherence avec secteur, ton et public cible.
Aucun texte hors JSON.
"""


def _sections_list(architecture: dict[str, Any]) -> str:
    sections = architecture.get("sections") or []
    lines = []
    for s in sections:
        sid   = s.get("id", "")
        stype = s.get("type", "")
        purpose = s.get("purpose", "")
        line = f"  - {sid} ({stype})"
        if purpose:
            line += f" : {purpose}"
        lines.append(line)
    return "\n".join(lines)


def build_content_user_prompt(ctx: BrandContext, architecture: dict[str, Any]) -> str:
    slogan_line = ctx.slogan or "(aucun slogan)"

    return (
        f"LANGUE : {ctx.language}\n"
        f"Marque : {ctx.brand_name} | Slogan exact : « {slogan_line} »\n"
        f"Secteur : {ctx.sector or '?'} | Cible : {ctx.target_audience or '?'}\n"
        f"Pitch : {ctx.short_pitch or ctx.description_brief or '?'}\n\n"
        f"SECTIONS A REMPLIR :\n{_sections_list(architecture)}\n\n"
        "Genere le contenu pour chaque section. Renvoie UNIQUEMENT le JSON."
    )
