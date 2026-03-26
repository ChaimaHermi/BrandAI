# ══════════════════════════════════════════════════════════════
# market_analysis_agent.py
#
# Pipeline en 4 stages :
#   Stage 1  — Query generator   (Llama 3.3 70B · Groq free)
#   Stage 2  — Tools parallel    (asyncio.gather · market_analysis_tools.py)
#   Stage 3  — Python cleaner    (0 LLM · BeautifulSoup · rapidfuzz)
#   Stage 4  — Synthesis LLM     (gpt-oss-120b · Groq free · 1 seul appel)
# ══════════════════════════════════════════════════════════════

import asyncio
import json
import logging
import os
import re
import unicodedata
from typing import Any

try:
    from config.settings import GROQ_KEYS
except ImportError:
    GROQ_KEYS = []

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# STAGE 3 — PYTHON DATA CLEANER (0 LLM)
# ══════════════════════════════════════════════════════════════

class DataCleaner:
    MAX_TOKENS_TOTAL   = 3_500
    MAX_TOKENS_SECTION = 600
    DEDUP_THRESHOLD    = 85

    def __init__(self, idea_keywords: list[str]):
        self.idea_keywords = [kw.lower() for kw in idea_keywords]

    def _count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        limit = max_tokens * 4
        return text[:limit] if len(text) > limit else text

    @staticmethod
    def _strip_html(text: str) -> str:
        if not text:
            return ""
        try:
            from bs4 import BeautifulSoup
            return BeautifulSoup(text, "lxml").get_text(separator=" ")
        except ImportError:
            return re.sub(r"<[^>]+>", " ", text)

    @staticmethod
    def _normalize(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"https?://\S+", "", text)
        text = re.sub(r"[^\w\s\.,;:!?'\"\-%()/€$]", " ", text)
        text = re.sub(r"\s+", " ", text)
        text = unicodedata.normalize("NFC", text)
        return text.strip()

    def _clean_text(self, text: str) -> str:
        return self._normalize(self._strip_html(text))

    def _relevance_score(self, text: str) -> float:
        if not text or not self.idea_keywords:
            return 0.0
        text_lower = text.lower()
        hits = sum(1 for kw in self.idea_keywords if kw in text_lower)
        return hits / len(self.idea_keywords)

    @staticmethod
    def _deduplicate(items: list[str], threshold: int = 85) -> list[str]:
        try:
            from rapidfuzz import fuzz
        except ImportError:
            seen = set()
            result = []
            for item in items:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            return result

        unique: list[str] = []
        for candidate in items:
            is_dup = any(
                fuzz.token_set_ratio(candidate, existing) >= threshold
                for existing in unique
            )
            if not is_dup:
                unique.append(candidate)
        return unique

    def _clean_search_results(self, data: dict, max_items: int = 6) -> list[dict]:
        results = data.get("results", [])
        cleaned = []
        for r in results:
            title   = self._clean_text(r.get("title", ""))
            snippet = self._clean_text(r.get("snippet", "") or r.get("description", ""))
            url     = r.get("url", "") or r.get("website", "")
            if not title:
                continue
            score = self._relevance_score(f"{title} {snippet}")
            cleaned.append({"title": title, "url": url, "snippet": snippet[:300], "relevance": score, "source": data.get("source", "")})
        cleaned.sort(key=lambda x: x["relevance"], reverse=True)
        return cleaned[:max_items]

    def _clean_articles(self, data: dict, max_items: int = 5) -> list[dict]:
        articles = data.get("articles", [])
        cleaned = []
        for a in articles:
            title = self._clean_text(a.get("title", ""))
            desc  = self._clean_text(a.get("description", ""))
            if not title or "[Removed]" in title:
                continue
            score = self._relevance_score(f"{title} {desc}")
            if score < 0.1:
                continue
            cleaned.append({"title": title, "source": a.get("source", ""), "date": a.get("published_at", ""), "description": desc[:250], "url": a.get("url", ""), "relevance": score})
        unique_titles = self._deduplicate([c["title"] for c in cleaned], self.DEDUP_THRESHOLD)
        deduped = [c for c in cleaned if c["title"] in unique_titles]
        deduped.sort(key=lambda x: x["relevance"], reverse=True)
        return deduped[:max_items]

    def _clean_maps(self, data: dict, max_items: int = 5) -> list[dict]:
        results = data.get("results", [])
        cleaned = []
        for r in results:
            name = self._clean_text(r.get("name", ""))
            if not name:
                continue
            cleaned.append({"name": name, "rating": r.get("rating", 0), "reviews": r.get("reviews", 0), "address": r.get("address", ""), "type": r.get("type", ""), "website": r.get("website", "")})
        return cleaned[:max_items]

    def _clean_youtube(self, data: dict, max_items: int = 5) -> list[dict]:
        videos = data.get("videos", [])
        cleaned = []
        for v in videos:
            title = self._clean_text(v.get("title", ""))
            desc  = self._clean_text(v.get("description", ""))
            if not title:
                continue
            score = self._relevance_score(f"{title} {desc}")
            if score < 0.05:
                continue
            cleaned.append({"title": title, "channel": v.get("channel", ""), "date": v.get("published_at", ""), "description": desc[:150], "score": score})
        cleaned.sort(key=lambda x: x["score"], reverse=True)
        return cleaned[:max_items]

    def _clean_tiktok(self, data: dict, max_items: int = 4) -> list[dict]:
        results = data.get("results", [])
        cleaned = []
        for v in results:
            title = self._clean_text(v.get("title", ""))
            if not title:
                continue
            hashtags = [h for h in v.get("hashtags", []) if isinstance(h, str)]
            cleaned.append({"title": title[:200], "likes": v.get("likes", 0), "plays": v.get("plays", 0), "hashtags": hashtags[:5], "score": self._relevance_score(title)})
        cleaned.sort(key=lambda x: x["plays"], reverse=True)
        return cleaned[:max_items]

    def _clean_trends(self, data: dict) -> dict:
        return {"keyword": data.get("keyword", ""), "direction": data.get("direction", "STABLE"), "signal_strength": data.get("signal_strength", "MEDIUM"), "avg_interest": data.get("avg_interest_last_month", 0), "related_rising": data.get("related_rising", [])[:5]}

    def _clean_worldbank(self, data: dict) -> dict:
        ind = data.get("indicators", {})
        return {
            "country_code": data.get("country_code", ""),
            "gdp_per_capita_usd": ind.get("gdp_per_capita"),
            "population": ind.get("population"),
            "internet_penetration_pct": ind.get("internet_pct"),
            "mobile_per100": ind.get("mobile_per100"),
            "urban_pct": ind.get("urban_pct"),
            "youth_labor_pct": ind.get("youth_pct"),
            # Données éducation réelles — remplacent les estimations LLM
            "tertiary_enrollment_pct": ind.get("tertiary_enrollment_pct"),
            "secondary_enrollment_pct": ind.get("secondary_enrollment_pct"),
            "literacy_rate_adult": ind.get("literacy_rate_adult"),
        }

    def clean(self, raw_data: dict) -> str:
        sections = []

        # 1. Concurrents web
        competitors = []
        for src in ["serp_competitors", "tavily"]:
            competitors.extend(self._clean_search_results(raw_data.get(src, {})))
        competitors.sort(key=lambda x: x["relevance"], reverse=True)
        seen = self._deduplicate([c["title"] for c in competitors], self.DEDUP_THRESHOLD)
        competitors = [c for c in competitors if c["title"] in seen][:8]
        if competitors:
            lines = ["### CONCURRENTS WEB"]
            for c in competitors:
                lines.append(f"- {c['title']} | {c['url']} | {c['snippet']}")
            sections.append("\n".join(lines))

        # 2. Acteurs locaux
        maps = self._clean_maps(raw_data.get("serp_maps", {}))
        if maps:
            lines = ["### ACTEURS LOCAUX (Google Maps)"]
            for m in maps:
                lines.append(f"- {m['name']} | rating:{m['rating']} ({m['reviews']} avis) | {m['type']} | {m['website']}")
            sections.append("\n".join(lines))

        # 3. Actualités
        news = self._clean_articles(raw_data.get("newsapi", {}))
        if news:
            lines = ["### ACTUALITÉS SECTORIELLES"]
            for a in news:
                lines.append(f"- [{a['date']}] {a['title']} ({a['source']}) : {a['description']}")
            sections.append("\n".join(lines))

        # 4. VOC Reddit
        reddit_results = self._clean_search_results(raw_data.get("reddit", {}))
        if reddit_results:
            lines = ["### VOC REDDIT"]
            for r in reddit_results:
                lines.append(f"- {r['title']} | {r['snippet']}")
            sections.append("\n".join(lines))

        # 5. Google Trends
        t1 = self._clean_trends(raw_data.get("trends_1", {}))
        t2 = self._clean_trends(raw_data.get("trends_2", {}))
        trends_lines = ["### GOOGLE TRENDS"]
        for t in [t1, t2]:
            if t.get("keyword"):
                related = ", ".join(t.get("related_rising", []))
                trends_lines.append(f"- #{t['keyword']} → {t['direction']} (signal:{t['signal_strength']}, intérêt:{t['avg_interest']}) | related: {related}")
        sections.append("\n".join(trends_lines))

        # 6. YouTube VOC
        yt = self._clean_youtube(raw_data.get("youtube", {}))
        if yt:
            lines = ["### YOUTUBE VOC"]
            for v in yt:
                lines.append(f"- {v['title']} | {v['channel']} [{v['date']}] | {v['description']}")
            sections.append("\n".join(lines))

        # 7. TikTok signaux
        tiktok = self._clean_tiktok(raw_data.get("tiktok", {}))
        if tiktok:
            lines = ["### TIKTOK SIGNAUX VIRAUX"]
            for v in tiktok:
                tags = " ".join(f"#{h}" for h in v.get("hashtags", []))
                lines.append(f"- {v['title']} | {v['plays']} vues | {tags}")
            sections.append("\n".join(lines))

        # 8. WorldBank macro
        wb = self._clean_worldbank(raw_data.get("worldbank", {}))
        if wb.get("country_code"):
            lines = ["### DONNÉES MACRO (WorldBank)"]
            lines.append(
                f"- Pays:{wb['country_code']} | PIB/hab:${wb.get('gdp_per_capita_usd','?')} "
                f"| Pop:{wb.get('population','?')} | Internet:{wb.get('internet_penetration_pct','?')}% "
                f"| Mobile:{wb.get('mobile_per100','?')}/100 | Urbain:{wb.get('urban_pct','?')}%"
            )
            # Calcul réel de la population étudiante depuis les indicateurs WorldBank
            # Évite que le LLM estime seul (ex: "15% étudiants" sans source)
            tert = wb.get("tertiary_enrollment_pct")
            sec  = wb.get("secondary_enrollment_pct")
            pop  = wb.get("population") or 0
            if tert is not None and pop:
                students_univ  = int(pop * tert / 100)
                students_lycee = int(pop * (sec or 0) / 100)
                lines.append(
                    f"- Population cible RÉELLE (WorldBank) : "
                    f"universitaires={students_univ:,} ({tert}% taux inscription supérieur) | "
                    f"lycéens={students_lycee:,} ({sec}% taux inscription secondaire) "
                    f"← utiliser ces chiffres pour calculer TAM/SAM, ne pas estimer"
                )
            sections.append("\n".join(lines))

        # 9. Réglementaire
        regulatory = self._clean_search_results(raw_data.get("regulatory", {}), max_items=4)
        if regulatory:
            lines = ["### RÉGLEMENTATION"]
            for r in regulatory:
                lines.append(f"- {r['title']} | {r['snippet']}")
            sections.append("\n".join(lines))

        # ── Assemblage avec budget tokens ─────────────────────
        context = "\n\n".join(sections)
        if self._count_tokens(context) > self.MAX_TOKENS_TOTAL:
            trimmed = []
            budget = self.MAX_TOKENS_TOTAL
            for section in sections:
                section_tokens = self._count_tokens(section)
                if section_tokens <= self.MAX_TOKENS_SECTION:
                    trimmed.append(section)
                    budget -= section_tokens
                else:
                    truncated = self._truncate_to_tokens(section, min(self.MAX_TOKENS_SECTION, budget))
                    trimmed.append(truncated)
                    budget -= self._count_tokens(truncated)
                if budget <= 100:
                    break
            context = "\n\n".join(trimmed)

        logger.info(f"[cleaner] contexte assemblé : {self._count_tokens(context)} tokens / {self.MAX_TOKENS_TOTAL} budget")
        return context


# ══════════════════════════════════════════════════════════════
# STAGE 1 — PROMPT : Query Generator (Llama 3.3 70B)
# ══════════════════════════════════════════════════════════════

QUERY_GENERATOR_PROMPT = """Tu es un expert en recherche de marché.
À partir d'une idée de projet, génère des requêtes de recherche optimisées pour 10 sources différentes.

OBJECTIF DE CHAQUE REQUÊTE :
- competitors  : trouver les NOMS des concurrents directs sur le marché cible
- maps         : trouver les acteurs physiques locaux avec ratings
- tavily       : trouver des CHIFFRES de marché — taille, revenus, CAGR, part de marché
                 → toujours inclure "market size" ou "revenue" ou "CAGR" ou "rapport" dans la requête
                 → toujours en anglais pour maximiser les résultats chiffrés
- reddit       : trouver des avis utilisateurs authentiques sur le problème
                 → toujours en anglais, toujours inclure "app" ou "tool" ou "software"
- news         : actualités récentes du secteur dans la langue locale
- trends_1     : mot-clé EXACT que les utilisateurs tapent (1-3 mots, langue locale)
- trends_2     : mot-clé alternatif ou concurrent direct (1-3 mots)
- youtube      : témoignages et reviews d'utilisateurs — inclure "review" ou "avis" ou "test"
- tiktok       : contenu viral du secteur — inclure hashtag ou terme populaire
- regulatory   : réglementations spécifiques au secteur et au pays cible

RÈGLES :
- Requêtes courtes et précises (3-8 mots)
- tavily et reddit : TOUJOURS en anglais pour maximiser les données chiffrées
- competitors, news, trends : dans la langue du marché cible
- Ne jamais inventer de noms d'entreprises
- Retourner UNIQUEMENT du JSON valide, sans backticks, sans texte avant/après

EXEMPLES POUR UNE APP EDTECH EN TUNISIE :
{
  "competitors":  "application emploi du temps étudiant Tunisie",
  "maps":         "cours particuliers Tunis",
  "tavily":       "EdTech student app market size MENA revenue 2024",
  "reddit":       "student schedule app review productivity tool",
  "news":         "startup EdTech Tunisie éducation numérique",
  "trends_1":     "emploi du temps étudiant",
  "trends_2":     "organisation scolaire",
  "youtube":      "application étudiant organisation avis test",
  "tiktok":       "étudiant organisation cours",
  "regulatory":   "protection données éducation Tunisie loi"
}

FORMAT DE RÉPONSE — même structure, adapter au projet fourni :
{
  "competitors": "...",
  "maps": "...",
  "tavily": "... market size revenue CAGR report 2024",
  "reddit": "... app review user opinion",
  "news": "...",
  "trends_1": "...",
  "trends_2": "...",
  "youtube": "... avis review test",
  "tiktok": "...",
  "regulatory": "..."
}
"""


# ══════════════════════════════════════════════════════════════
# STAGE 4 — PROMPT : Synthesis LLM (gpt-oss-120b)
# ══════════════════════════════════════════════════════════════

SYNTHESIS_PROMPT = """Tu es un analyste de marché senior.
À partir des données collectées ci-dessous, génère une analyse de marché complète et structurée.

RÈGLES ABSOLUES :
- Répondre UNIQUEMENT en JSON valide, sans backticks, sans texte avant/après
- Baser chaque affirmation sur les données fournies
- Porter et Gartner DOIVENT être remplis — utiliser les concurrents identifiés pour les positionner

RÈGLE TAM/SAM — UNITÉ ET ESTIMATION :
- tam et sam sont en MILLIARDS USD (ex: 1.84 = $1.84B, 0.18 = $180M)
- Si les données directes sont absentes, estimer via : population_cible × taux_adoption × ARPU_secteur
- JAMAIS laisser tam ou sam à null ou 0

RÈGLE SOM — CALCUL OBLIGATOIRE :
- sam_base = valeur absolue du SAM en USD (ex: 550000000 pour $550M)
- conservateur = sam_base × 0.005   ← toujours 0.5%
- realiste     = sam_base × 0.01    ← toujours 1%
- optimiste    = sam_base × 0.03    ← toujours 3%
- JAMAIS utiliser d'autres pourcentages

RÈGLE GARTNER — POSITIONNEMENT OBLIGATOIRE :
- Positionner les concurrents trouvés dans les 4 quadrants :
  vision_score    = capacité d'innovation et roadmap (1-10)
  execution_score = taille, ressources, part de marché (1-10)
- JAMAIS laisser tous les quadrants vides

RÈGLE THREAT_SCORE — CALCUL OBLIGATOIRE :
- taille_acteur(40%) + adéquation_marché_cible(30%) + capacité_exécution(30%) → 0 à 100
- JAMAIS laisser threat_score à null

FORMAT JSON REQUIS :
{
  "sector": "nom du secteur",
  "kpis": {
    "tam": 1.84,
    "sam": 0.55,
    "cagr_pct": 25,
    "recommended_pricing_model": "modèle basé sur les concurrents et le marché",
    "market_maturity_score": 35
  },
  "som": {
    "sam_base": 550000000,
    "conservateur": 2750000,
    "realiste": 5500000,
    "optimiste": 16500000,
    "confidence": "low | medium | high",
    "note": "hypothèse : population × taux_adoption × ARPU — confidence low car données directes absentes"
  },
  "porter": {
    "rivalry":      {"score": 3, "level": "medium", "summary": "une phrase basée sur les données"},
    "new_entrants": {"score": 4, "level": "high",   "summary": "une phrase basée sur les données"},
    "substitutes":  {"score": 3, "level": "medium", "summary": "une phrase basée sur les données"},
    "buyers":       {"score": 3, "level": "medium", "summary": "une phrase basée sur les données"},
    "suppliers":    {"score": 1, "level": "low",    "summary": "une phrase basée sur les données"}
  },
  "gartner": {
    "quadrants": {
      "leaders":      [{"name": "nom", "vision_score": 8, "execution_score": 9}],
      "challengers":  [{"name": "nom", "vision_score": 5, "execution_score": 8}],
      "visionaries":  [{"name": "nom", "vision_score": 8, "execution_score": 5}],
      "niche_players":[{"name": "nom", "vision_score": 4, "execution_score": 4}]
    },
    "our_position": {"quadrant": "visionaries", "vision_score": 7, "execution_score": 4, "rationale": "une phrase"}
  },
  "competitors": [
    {
      "name": "nom du concurrent",
      "url": "url ou null",
      "type": "direct | indirect",
      "strengths": ["force 1", "force 2"],
      "weaknesses": ["faiblesse 1", "faiblesse 2"],
      "threat_score": 70,
      "data_source": "source API"
    }
  ],
  "competitive_positioning": {
    "main_gap": "gap principal identifié dans les données",
    "differentiation_angle": "angle de différenciation suggéré",
    "weakest_competitor": "concurrent le plus faible et pourquoi",
    "local_advantage": "avantage local si applicable",
    "threat_level": "low | medium | high"
  },
  "trends": [
    {"keyword": "mot-clé", "direction": "RISING | STABLE | FALLING", "signal_strength": "HIGH | MEDIUM | LOW", "insight": "2 phrases", "data_source": "source"}
  ],
  "voice_of_customer": {
    "top_pain_points": ["pain point 1", "pain point 2", "pain point 3"],
    "desired_features": ["feature 1", "feature 2", "feature 3"],
    "competitor_frustrations": ["frustration 1", "frustration 2"],
    "youtube_voc_signals": ["signal 1", "signal 2"],
    "tiktok_signals": ["signal 1"],
    "sources": ["sources utilisées"]
  },
  "swot": {
    "strengths": ["force 1", "force 2", "force 3"],
    "weaknesses": ["faiblesse 1", "faiblesse 2"],
    "opportunities": ["opportunité 1", "opportunité 2", "opportunité 3"],
    "threats": ["menace 1", "menace 2", "menace 3"]
  },
  "risks": [
    {"category": "competition | regulatory | technology | market | financial", "description": "description", "severity": "HIGH | MEDIUM | LOW", "mitigation": "mitigation"}
  ],
  "opportunities": [
    {"title": "titre", "description": "description", "time_horizon": "short (0-6m) | medium (6-18m) | long (18m+)"}
  ],
  "market_entry_signal": {
    "timing": "now | wait | avoid",
    "timing_rationale": "justification basée sur les données",
    "key_risks_to_enter": ["risque 1", "risque 2"],
    "key_enablers": ["enabler 1", "enabler 2"],
    "first_action": "première action concrète recommandée"
  },
  "regulatory": {
    "key_regulations": ["réglementation 1"],
    "entry_barriers": ["barrière 1"],
    "compliance_risks": ["risque 1"],
    "regulatory_outlook": "favorable | neutral | unfavorable",
    "licenses_required": ["licence 1"]
  },
  "recommendations": [
    {"title": "titre", "description": "description", "priority": "HIGH | MEDIUM | LOW", "rationale": "justification"}
  ],
  "go_no_go": {
    "verdict": "GO | GO CONDITIONNEL | NO-GO",
    "confidence": 7,
    "main_reasons": ["raison 1", "raison 2"],
    "conditions": ["condition 1"],
    "rationale": "justification globale"
  },
  "data_quality": {
    "sources_used": ["sources effectivement utilisées"],
    "confidence_score": 7,
    "missing_data_notes": "données manquantes ou insuffisantes"
  }
}
"""


# ══════════════════════════════════════════════════════════════
# LLM CALLER (compatible Groq SDK)
# ══════════════════════════════════════════════════════════════

async def _call_groq(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    try:
        from groq import AsyncGroq
    except ImportError:
        raise RuntimeError("groq non installé : pip install groq")

    # FIX 1 : fallback os.getenv si GROQ_KEYS vide
    key = GROQ_KEYS[0] if GROQ_KEYS else os.getenv("GROQ_API_KEY", "")
    if not key:
        raise RuntimeError("Aucune GROQ_API_KEY configurée dans .env ou config.settings")

    client = AsyncGroq(api_key=key)
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def _parse_json_safe(raw: str) -> dict:
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            return json.loads(match.group(0))
        raise ValueError(f"Impossible de parser le JSON : {raw[:200]}")


# ══════════════════════════════════════════════════════════════
# MARKET ANALYSIS AGENT
# ══════════════════════════════════════════════════════════════

class MarketAnalysisAgent:
    """
    Agent analyse de marché — pipeline 4 stages.

    Usage :
        agent = MarketAnalysisAgent()
        result = await agent.run(
            idea="Plateforme tutorat en ligne Tunisie",
            country_code="TN",
            language="fr",
        )
    """

    MODEL_QUERIES   = "llama-3.3-70b-versatile"  # Stage 1 — Groq free
    MODEL_SYNTHESIS = "openai/gpt-oss-120b"       # Stage 4 — Groq free

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def _stage1_generate_queries(self, idea: str, country_code: str, language: str) -> dict:
        user_prompt = (
            f"Idée de projet : {idea}\n"
            f"Pays cible : {country_code}\n"
            f"Langue du marché : {language}\n\n"
            "Génère les 10 requêtes de recherche adaptées à ce projet et ce marché."
        )
        self.logger.info("[stage1] génération des queries...")
        raw = await _call_groq(
            system_prompt=QUERY_GENERATOR_PROMPT,
            user_prompt=user_prompt,
            model=self.MODEL_QUERIES,
            temperature=0.2,
            max_tokens=512,
        )
        queries = _parse_json_safe(raw)
        self.logger.info(f"[stage1] {len(queries)} queries générées")
        return queries

    async def _stage2_fetch_data(self, queries: dict, country_code: str) -> dict:
        from tools.market_tools import run_all_tools
        self.logger.info("[stage2] fetch parallèle des APIs...")
        raw_data = await run_all_tools(queries, country_code)
        sources_ok = [k for k, v in raw_data.items() if not v.get("error")]
        self.logger.info(f"[stage2] {len(sources_ok)}/{len(raw_data)} sources OK")
        return raw_data

    def _stage3_clean(self, raw_data: dict, idea: str) -> str:
        keywords = re.findall(r"\b\w{3,}\b", idea.lower())
        keywords = list(set(keywords))[:10]
        cleaner = DataCleaner(idea_keywords=keywords)
        context = cleaner.clean(raw_data)
        self.logger.info(f"[stage3] contexte nettoyé : {len(context)} chars")
        return context

    async def _stage4_synthesize(self, idea: str, country_code: str, context: str) -> dict:
        user_prompt = (
            f"PROJET ANALYSÉ : {idea}\n"
            f"PAYS / MARCHÉ CIBLE : {country_code}\n\n"
            "DONNÉES COLLECTÉES :\n"
            f"{context}\n\n"
            "Génère l'analyse de marché complète en JSON."
        )
        self.logger.info("[stage4] synthèse LLM...")
        raw = await _call_groq(
            system_prompt=SYNTHESIS_PROMPT,
            user_prompt=user_prompt,
            model=self.MODEL_SYNTHESIS,
            temperature=0.3,
            max_tokens=4096,
        )
        result = _parse_json_safe(raw)
        self.logger.info("[stage4] JSON synthèse OK")
        return result

    async def run(self, idea: str, country_code: str = "FR", language: str = "fr") -> dict:
        self.logger.info(f"[agent] démarrage → idée='{idea}' pays={country_code}")

        queries  = await self._stage1_generate_queries(idea, country_code, language)
        raw_data = await self._stage2_fetch_data(queries, country_code)
        context  = self._stage3_clean(raw_data, idea)
        result   = await self._stage4_synthesize(idea, country_code, context)

        result["_meta"] = {
            "idea": idea,
            "country_code": country_code,
            "queries_used": queries,
            "sources_fetched": list(raw_data.keys()),
            "context_chars": len(context),
        }

        self.logger.info(f"[agent] terminé → verdict={result.get('go_no_go', {}).get('verdict', '?')}")
        return result