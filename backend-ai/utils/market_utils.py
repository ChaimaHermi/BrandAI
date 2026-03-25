# ══════════════════════════════════════════════════════════════
#  market_utils.py  —  BrandAI
#  Génère des queries adaptées par outil via LLM
#
#  CORRECTIONS vs version précédente :
#  - Queries générées par LLM (plus statiques)
#  - Tavily + Serper ajoutés
#  - Langue adaptée au pays (FR/AR/EN)
#  - Queries spécialisées par API avec bonnes règles syntaxiques
#  - Fallback statique si LLM indisponible
# ══════════════════════════════════════════════════════════════

import os
import json
import logging
from groq import AsyncGroq

logger = logging.getLogger("brandai.market_utils")

# ══════════════════════════════════════════════════════════════
# SYSTEM PROMPT — LLM génère les queries
# ══════════════════════════════════════════════════════════════

QUERY_GEN_SYSTEM = """Tu es un expert en market research, SEO et recherche d'informations.

Ta mission : générer des requêtes de recherche OPTIMISÉES pour chaque API
à partir d'une idée de startup.

RÈGLES CRITIQUES PAR API :

1. serpapi_local (Google Search — concurrents locaux) :
   - Langue du marché cible (FR si Tunisie/Maroc, AR si marché arabe)
   - Connecteurs autorisés : OR, -, "expression exacte"
   - Exemple : "plateforme e-learning OR formation en ligne Tunisie -Coursera"
   - MAX 4 requêtes, 3-7 mots chacune

2. serpapi_global (Google Search — benchmarks internationaux) :
   - EN uniquement
   - Exemple : "best edtech platform Africa 2025" OR "online learning startup funding"
   - MAX 3 requêtes

3. serpapi_maps (Google Maps — concurrents locaux avec ratings) :
   - Langue locale, nom secteur + ville/pays
   - Exemple : "plateforme formation en ligne Tunis"
   - MAX 2 requêtes

4. tavily_competitor (recherche web enrichie) :
   - Phrases naturelles longues, questions directes
   - Exemple : "what are the main competitors of e-learning platforms in North Africa 2025"
   - MAX 3 requêtes, 8-15 mots

5. tavily_voc (Voice of Customer — Reddit + Quora) :
   - EN obligatoire + mots d'intention (problems/why/frustrated/complaints/hate/best)
   - Préfixe site: pour cibler : "site:reddit.com e-learning frustrations problems"
   - Exemple : "site:quora.com what features should online learning platform have"
   - MAX 3 requêtes

6. serpapi_trends (Google Trends) :
   - 1-3 MOTS MAXIMUM — OBLIGATOIRE — plus long = 0 résultats
   - Exemple : "e-learning" ou "edtech" ou "formation en ligne"
   - MAX 3 mots-clés

7. serpapi_tiktok (TikTok signaux viraux) :
   - 1-3 mots EN
   - Exemple : "edtech" "online learning"
   - MAX 2 mots-clés

8. youtube (YouTube vidéos populaires) :
   - EN, 3-5 mots, focus comportement utilisateur
   - Exemple : "online learning platform review"
   - MAX 3 requêtes

9. newsapi (actualités secteur) :
   - FR ou EN, 3-6 mots
   - Exemple : "EdTech Afrique financement 2025"
   - MAX 3 requêtes

10. regulatory (réglementation) :
    - Langue locale + termes légaux
    - Exemple : "réglementation formation en ligne Tunisie loi"
    - MAX 2 requêtes

FORMAT DE SORTIE — JSON STRICT :
{
  "serpapi_local": ["requête FR 1", "requête FR 2", "requête 3", "requête 4"],
  "serpapi_global": ["EN query 1", "EN query 2", "EN query 3"],
  "serpapi_maps": ["requête locale 1", "requête locale 2"],
  "tavily_competitor": ["phrase naturelle EN 1", "phrase 2", "phrase 3"],
  "tavily_voc": ["site:reddit.com EN query 1", "site:quora.com EN query 2", "EN query 3"],
  "serpapi_trends": ["keyword1", "keyword2", "keyword3"],
  "serpapi_tiktok": ["keyword1", "keyword2"],
  "youtube": ["EN query 1", "EN query 2", "EN query 3"],
  "newsapi": ["requête 1", "EN query 2", "requête 3"],
  "regulatory": ["requête locale 1", "EN query 2"],
  "country_code": "TN",
  "country": "Tunisie",
  "main_language": "fr"
}"""


# ══════════════════════════════════════════════════════════════
# GÉNÉRATEUR LLM
# ══════════════════════════════════════════════════════════════

async def build_queries(
    problem: str,
    target: str,
    sector: str = "",
    solution: str = "",
    country: str = "Tunisie",
    country_code: str = "TN",
    language: str = "fr",
) -> dict:
    """
    Génère les queries adaptées via LLM.
    Fallback statique si LLM indisponible.
    """
    logger.info(f"[query_gen] Building queries — sector={sector} country={country}")

    groq_key = (
        os.getenv("GROQ_API_KEY", "")
        or os.getenv("GROQ_API_KEY_2", "")
        or os.getenv("GROQ_API_KEY_3", "")
    )

    if not groq_key:
        logger.warning("[query_gen] No Groq key — using static fallback")
        return _static_fallback(problem, target, sector, solution, country, country_code, language)

    client = AsyncGroq(api_key=groq_key)

    user_prompt = f"""Génère les requêtes optimisées pour cette startup :

Problème résolu : {problem}
Solution proposée : {solution}
Secteur : {sector}
Cible : {target}
Pays principal : {country} ({country_code})
Langue marché : {language}

Applique les règles de syntaxe par API définies dans le system prompt.
Adapte la langue selon le pays ({country}) et l'API."""

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": QUERY_GEN_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=700,
        )

        content = response.choices[0].message.content.strip()

        # Nettoyage backticks si LLM les ajoute
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        queries = json.loads(content)
        queries = _validate_queries(queries, problem, target, sector, solution, country, country_code, language)

        logger.info(
            f"[query_gen] LLM queries generated — "
            f"serpapi:{len(queries.get('serpapi_local',[]))} "
            f"tavily:{len(queries.get('tavily_competitor',[]))} "
            f"voc:{len(queries.get('tavily_voc',[]))}"
        )
        return queries

    except json.JSONDecodeError as e:
        logger.warning(f"[query_gen] JSON parse error: {e} — using fallback")
        return _static_fallback(problem, target, sector, solution, country, country_code, language)
    except Exception as e:
        logger.warning(f"[query_gen] LLM error: {e} — using fallback")
        return _static_fallback(problem, target, sector, solution, country, country_code, language)


# ══════════════════════════════════════════════════════════════
# FALLBACK STATIQUE
# ══════════════════════════════════════════════════════════════

def _static_fallback(
    problem: str,
    target: str,
    sector: str,
    solution: str,
    country: str,
    country_code: str,
    language: str,
) -> dict:
    """Queries statiques de secours si LLM indisponible."""
    ctx = sector or problem[:40]
    sol = solution[:40] if solution else ctx

    return {
        "serpapi_local": [
            f"{ctx} {country}",
            f"meilleure application {ctx}",
            f"{ctx} plateforme startup {country}",
            f'{ctx} OR "{sol}" {country}',
        ],
        "serpapi_global": [
            f"best {ctx} platform 2025",
            f"{ctx} startup funding Africa",
            f"{ctx} market leaders",
        ],
        "serpapi_maps": [
            f"{ctx} {country}",
            f"agence {ctx} {country}",
        ],
        "tavily_competitor": [
            f"what are the main competitors of {ctx} in {country} 2025",
            f"best {ctx} platforms North Africa market analysis",
            f"{ctx} startup ecosystem funding {country}",
        ],
        "tavily_voc": [
            f"site:reddit.com {ctx} problems frustrated users",
            f"site:quora.com what features should {ctx} platform have",
            f"why students quit {ctx} apps complaints",
        ],
        "serpapi_trends": [
            ctx[:20],
            sol[:20],
            "online" if "ligne" in problem.lower() else ctx[:15],
        ],
        "serpapi_tiktok": [
            ctx[:15],
            "edtech" if "tech" in ctx.lower() else ctx[:10],
        ],
        "youtube": [
            f"{ctx} tutorial review",
            f"how to {problem[:25]}",
            f"{ctx} {country} 2025",
        ],
        "newsapi": [
            f"{ctx} startup {country} 2025",
            f"{ctx} funding investment Africa",
            f"{ctx} market news 2025",
        ],
        "regulatory": [
            f"réglementation {ctx} {country} loi",
            f"{ctx} compliance regulation {country_code}",
        ],
        "country_code": country_code,
        "country": country,
        "main_language": language,
    }


# ══════════════════════════════════════════════════════════════
# VALIDATION
# ══════════════════════════════════════════════════════════════

def _validate_queries(
    queries: dict,
    problem: str,
    target: str,
    sector: str,
    solution: str,
    country: str,
    country_code: str,
    language: str,
) -> dict:
    """Valide et complète les queries générées par le LLM."""

    fallback = _static_fallback(problem, target, sector, solution, country, country_code, language)

    required = [
        "serpapi_local", "serpapi_global", "serpapi_maps",
        "tavily_competitor", "tavily_voc",
        "serpapi_trends", "serpapi_tiktok",
        "youtube", "newsapi", "regulatory",
    ]

    for key in required:
        if key not in queries or not isinstance(queries[key], list) or len(queries[key]) == 0:
            logger.warning(f"[query_gen] Missing '{key}' — using fallback")
            queries[key] = fallback[key]

    # Limits par groupe
    limits = {
        "serpapi_local": 4, "serpapi_global": 3, "serpapi_maps": 2,
        "tavily_competitor": 3, "tavily_voc": 3,
        "serpapi_trends": 3, "serpapi_tiktok": 2,
        "youtube": 3, "newsapi": 3, "regulatory": 2,
    }
    for key, limit in limits.items():
        if key in queries:
            queries[key] = queries[key][:limit]

    # Validation trends — 1-3 mots max
    cleaned_trends = []
    for kw in queries.get("serpapi_trends", []):
        words = kw.strip().split()
        if len(words) <= 3:
            cleaned_trends.append(kw)
        else:
            cleaned_trends.append(" ".join(words[:3]))
            logger.warning(f"[query_gen] Trends query truncated: '{kw}' → '{cleaned_trends[-1]}'")
    queries["serpapi_trends"] = cleaned_trends

    # Metadata
    queries.setdefault("country_code", country_code)
    queries.setdefault("country", country)
    queries.setdefault("main_language", language)

    return queries