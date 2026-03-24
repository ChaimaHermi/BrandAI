# ══════════════════════════════════════════════════════════════
#  market_prompts.py
#  Prompts pour le Market Analysis Agent
# ══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """Tu es un expert senior en analyse de marché et stratégie startup.

Tu analyses des données issues de plusieurs sources :
- SerpAPI       : concurrents, signaux marché
- YouTube       : comportement utilisateur, contenu populaire
- NewsAPI       : tendances, funding, régulation
- Reddit        : pain points réels, frustrations utilisateurs
- Google Trends : évolution de la demande
- World Bank    : contexte macro (PIB, internet, mobile)

OBJECTIF : Produire une analyse stratégique complète, honnête et actionnelle.

RÈGLES ABSOLUES :
1. Répond UNIQUEMENT avec du JSON valide — aucun texte avant ou après
2. Ne jamais inventer de données — si une info manque, note-le dans data_quality
3. Baser chaque insight sur les données fournies, pas sur des suppositions
4. Être logique, structuré, et business-oriented

PRIORITÉS D'ANALYSE :
1. Pain points utilisateurs (Reddit) → ce que les gens veulent vraiment
2. Tendances (Trends + News) → timing du marché
3. Concurrence (SerpAPI) → positionnement différenciant
4. Contexte macro (World Bank) → faisabilité locale
"""


def build_user_prompt(data: dict) -> str:

    # On sérialise chaque section séparément pour éviter les problèmes f-string
    import json

    idea_str        = json.dumps(data.get("idea", {}), ensure_ascii=False, indent=2)
    competitors_str = json.dumps(data.get("raw_competitors", []), ensure_ascii=False, indent=2)
    organic_str     = json.dumps(data.get("organic_signals", []), ensure_ascii=False, indent=2)
    youtube_str     = json.dumps(data.get("top_youtube_signals", []), ensure_ascii=False, indent=2)
    news_str        = json.dumps(data.get("news_articles", []), ensure_ascii=False, indent=2)
    funding_str     = json.dumps(data.get("funding_signals", []), ensure_ascii=False, indent=2)
    regulatory_str  = json.dumps(data.get("regulatory_signals", []), ensure_ascii=False, indent=2)
    pain_str        = json.dumps(data.get("reddit_pain_points", []), ensure_ascii=False, indent=2)
    mentions_str    = json.dumps(data.get("competitor_mentions", []), ensure_ascii=False, indent=2)
    trends_str      = json.dumps(data.get("growth_trends", []), ensure_ascii=False, indent=2)
    macro_str       = json.dumps(data.get("macro_context", {}), ensure_ascii=False, indent=2)

    output_schema = """{
  "market_overview": {
    "sector": "string",
    "tam_global_usd": "string (ex: $43B)",
    "tam_cagr_pct": 0,
    "sam_local_usd": "string",
    "sam_rationale": "string — comment tu as estimé le SAM local",
    "market_maturity_score": 0,
    "market_maturity_label": "nascent | growing | mature | saturated",
    "timing_signal": "string — pourquoi maintenant est le bon moment (ou pas)"
  },

  "competitors": [
    {
      "name": "string",
      "url": "string",
      "type": "direct | indirect | substitute",
      "strengths": ["string"],
      "weaknesses": ["string"],
      "threat_score": 0,
      "data_source": "string"
    }
  ],

  "swot": {
    "strengths":     ["string"],
    "weaknesses":    ["string"],
    "opportunities": ["string"],
    "threats":       ["string"]
  },

  "trends": [
    {
      "keyword":         "string",
      "direction":       "RISING | STABLE | DECLINING",
      "signal_strength": "HIGH | MEDIUM | LOW",
      "insight":         "string — ce que ça implique pour le projet",
      "data_source":     "string"
    }
  ],

  "voice_of_customer": {
    "top_pain_points":        ["string"],
    "desired_features":       ["string"],
    "competitor_frustrations": ["string"],
    "sources":                ["string"]
  },

  "risks": [
    {
      "category":    "regulatory | market | technology | competition",
      "description": "string",
      "severity":    "HIGH | MEDIUM | LOW",
      "mitigation":  "string"
    }
  ],

  "opportunities": [
    {
      "title":        "string",
      "description":  "string",
      "time_horizon": "short (0-6m) | medium (6-18m) | long (18m+)"
    }
  ],

  "kpis": {
    "addressable_students_local":  0,
    "internet_penetration_pct":    0,
    "mobile_penetration_per100":   0,
    "gdp_per_capita_usd":          0,
    "recommended_pricing_model":   "string",
    "estimated_cac_usd":           "string",
    "market_maturity_score":       0
  },

  "recommendations": [
    {
      "title":       "string",
      "description": "string — actionnable et spécifique",
      "priority":    "HIGH | MEDIUM | LOW",
      "rationale":   "string — basé sur quelle donnée"
    }
  ],

  "data_quality": {
    "sources_used":       ["serpapi", "youtube", "newsapi", "reddit", "google_trends", "worldbank"],
    "confidence_score":   0,
    "missing_data_notes": "string — ce qui manque pour une analyse plus précise"
  }
}"""

    return f"""
=== IDEA ===
{idea_str}

=== COMPETITORS (SERPAPI) ===
{competitors_str}

=== ORGANIC SIGNALS (SERPAPI) ===
{organic_str}

=== YOUTUBE SIGNALS ===
{youtube_str}

=== NEWS ARTICLES ===
{news_str}

=== FUNDING SIGNALS ===
{funding_str}

=== REGULATORY SIGNALS ===
{regulatory_str}

=== REDDIT PAIN POINTS ===
{pain_str}

=== COMPETITOR MENTIONS (REDDIT) ===
{mentions_str}

=== GOOGLE TRENDS ===
{trends_str}

=== MACRO CONTEXT (WORLD BANK) ===
{macro_str}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TASK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Analyse ces données et produis une analyse marché complète.

INSTRUCTIONS :
- Ne résume pas → analyse et déduis des insights business
- Pour le TAM/SAM : utilise les données World Bank + Trends pour estimer localement
- Pour les concurrents : base-toi sur SerpAPI, classe par threat_score réel
- Pour voice_of_customer : base-toi UNIQUEMENT sur Reddit (source la plus honnête)
- Pour confidence_score : sois honnête (0=aucune donnée, 100=données parfaites)
- Si une donnée manque, note-le dans missing_data_notes, ne l'invente pas

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT — JSON STRICT (aucun texte avant/après)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{output_schema}
"""