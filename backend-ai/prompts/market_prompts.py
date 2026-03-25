# ══════════════════════════════════════════════════════════════
#  market_prompts.py  —  BrandAI
#
#  CORRECTIONS vs version précédente :
#  + SYSTEM_PROMPT enrichi : LLM interprète les données
#    en se basant sur TOUTE l'idée (problem + solution + pitch + target)
#  + INSTRUCTIONS enrichies : calculs TAM/SAM obligatoires
#  + Règle explicite addressable_market_local non nul
#  + tiktok_signals doit être [] pas ""
# ══════════════════════════════════════════════════════════════

import json

SYSTEM_PROMPT = """Tu es un expert senior en analyse de marché et stratégie startup.

Tu analyses des données issues de plusieurs sources :
- SerpAPI Google Search  : concurrents directs + signaux marché (local FR + global EN)
- SerpAPI Google Maps    : ratings et avis concurrents locaux
- SerpAPI Google Trends  : évolution de la demande par mot-clé (1-12 mois)
- SerpAPI TikTok         : signaux viraux et tendances contenu
- Tavily Search          : résumés enrichis concurrents + actualités (optimisé LLM)
- YouTube Data API       : comportement utilisateur, contenu populaire, VOC vidéo
- NewsAPI + Newsdata.io  : actualités secteur FR/EN/AR, funding, régulation
- Reddit via Tavily      : pain points réels, frustrations utilisateurs
- World Bank API         : contexte macro (PIB, internet, mobile, population)
- Regulatory data        : cadre légal, conformité, barrières à l'entrée

OBJECTIF : Produire une analyse stratégique complète, honnête et actionnelle,
entièrement rédigée en français, avec un verdict go/no-go justifié.

CONTEXTE CRITIQUE — LIS L'IDÉE EN ENTIER :
Tu vas recevoir une idée complète avec : problem, solution, pitch, target, sector, country.
Tu dois analyser les données EN FONCTION DE CETTE IDÉE PRÉCISE, pas du secteur en général.
Exemple : si l'idée est "tutorat en ligne pour étudiants tunisiens", interprète chaque
donnée sous l'angle de cette solution spécifique pour ce marché spécifique.
- Le problem définit les pain points à chercher dans le VOC
- La solution définit les concurrents directs vs indirects
- Le target définit le profil macro à croiser (âge, géographie)
- Le country définit le cadre réglementaire et les APIs locales

RÈGLES ABSOLUES :
1. Répond UNIQUEMENT avec du JSON valide — aucun texte avant ou après
2. Guillemets droits " uniquement (jamais " " ' '), pas de virgule après le dernier élément
3. CRITIQUE : aucun saut de ligne dans une valeur string.
   Champs longs (sam_rationale, timing_signal, go_no_go.rationale, missing_data_notes) :
   UNE seule ligne, max 350 caractères. Sinon JSON invalide.
4. Inclure TOUS les champs du schéma (valeurs "", 0, [] si non déductibles)
5. Ne jamais inventer de faits chiffrés — note dans missing_data_notes si manquant
6. Baser chaque insight sur les données fournies ET sur le contexte de l'idée
7. LANGUE FRANÇAISE : tout le contenu textuel en français.
   Exceptions : noms de marques, URLs, codes ISO, symboles ($, USD), termes techniques.
8. tiktok_signals doit être un tableau [] même si vide — jamais une chaîne ""
9. addressable_market_local DOIT être calculé si population + internet + youth disponibles :
   addressable_market_local = population × (internet_penetration/100) × (youth_pct/100)
   Ne jamais laisser à 0 si les données World Bank sont présentes.
10. tam_global_usd DOIT être estimé si CAGR ou taille secteur mentionnés dans les données.
    Format : "$X B" ou "$X M". Si vraiment impossible, écris "Non estimé" avec justification.
11. competitive_positioning : base-toi UNIQUEMENT sur les noms et snippets des concurrents fournis + VOC Reddit/YouTube. N'invente aucun chiffre. Cite le nom du concurrent réel.
12. market_entry_signal.timing : déduis depuis les trends (RISING = now/urgent, DECLINING = wait) + funding signals (concurrent qui lève = urgent) + regulatory (barrière = wait). Une seule règle logique, pas de chiffre inventé.

PRIORITÉS D'ANALYSE (ordre décroissant d'importance) :
1. Voice of Customer : Reddit + YouTube → frustrations, besoins liés AU PROBLEM de l'idée
2. Tendances : Google Trends + TikTok + News → timing et momentum pour CETTE solution
3. Concurrence : SerpAPI + Tavily + Maps → concurrents de CETTE solution pour CE marché
4. Positionnement : compétiteurs + VOC → gap réel et angle de différenciation
5. Entrée marché : timing (trends + funding + regulatory) → now/wait/urgent
6. Réglementaire : cadre légal du pays cible → risques spécifiques à CETTE activité
7. Macro : World Bank → faisabilité locale pour CE pays et CE target
"""

# ══════════════════════════════════════════════════════════════
# SCHÉMA JSON DE SORTIE
# ══════════════════════════════════════════════════════════════

OUTPUT_SCHEMA = """{
  "market_overview": {
    "sector": "string",
    "tam_global_usd": "string (ex: $43B — OBLIGATOIRE, estimer si données disponibles)",
    "tam_cagr_pct": 0,
    "sam_local_usd": "string",
    "sam_rationale": "string — calcul : population × internet × youth × ARPU estimé (une ligne)",
    "market_maturity_score": 0,
    "market_maturity_label": "nascent | growing | mature | saturated",
    "timing_signal": "string — pourquoi maintenant pour CETTE solution dans CE pays (une ligne)"
  },

  "competitors": [
    {
      "name": "string",
      "url": "string",
      "type": "direct | indirect | substitute",
      "strengths": ["string"],
      "weaknesses": ["string"],
      "threat_score": 0,
      "local_rating": 0,
      "data_source": "string"
    }
  ],

  "swot": {
    "strengths":     ["string — force spécifique à CETTE solution"],
    "weaknesses":    ["string — faiblesse spécifique à CETTE solution"],
    "opportunities": ["string — opportunité pour CE marché"],
    "threats":       ["string — menace pour CETTE activité dans CE pays"]
  },

  "trends": [
    {
      "keyword":         "string",
      "direction":       "RISING | STABLE | DECLINING",
      "signal_strength": "HIGH | MEDIUM | LOW",
      "insight":         "string — implication concrète pour CETTE idée (une ligne)",
      "data_source":     "google_trends | tiktok | news | youtube"
    }
  ],

  "voice_of_customer": {
    "top_pain_points":         ["string — liés au PROBLEM de l'idée"],
    "desired_features":        ["string — besoins liés à la SOLUTION proposée"],
    "competitor_frustrations": ["string — frustrations avec les alternatives actuelles"],
    "youtube_voc_signals":     ["string — thèmes UNIQUEMENT issus de YouTube"],
    "tiktok_signals":          [],
    "sources":                 ["string"]
  },

  "competitive_positioning": {
    "main_gap": "string — ce qui manque chez les concurrents identifiés",
    "differentiation_angle": "string — comment se différencier concrètement",
    "weakest_competitor": "string — nom + pourquoi il est vulnérable",
    "local_advantage": "string — avantage spécifique au marché local identifié",
    "threat_level": "low | medium | high",
    "sources": ["string"]
  },

  "market_entry_signal": {
    "timing": "now | wait | urgent",
    "timing_rationale": "string — basé sur Trends + News + Regulatory (une ligne)",
    "key_risks_to_enter": ["string — risque concret identifié dans les données"],
    "key_enablers": ["string — facteur favorable identifié dans les données"],
    "first_action": "string — première action concrète recommandée"
  },

  "regulatory": {
    "key_regulations": ["string — loi applicable dans LE PAYS CIBLE"],
    "entry_barriers":  ["string — barrière spécifique à CETTE activité"],
    "compliance_risks":["string — risque de conformité pour CE business model"],
    "regulatory_outlook": "favorable | neutre | contraignant",
    "licenses_required":  ["string — licence requise pour opérer légalement"]
  },

  "risks": [
    {
      "category":    "regulatory | market | technology | competition",
      "description": "string — risque contextualisé pour CETTE idée",
      "severity":    "HIGH | MEDIUM | LOW",
      "mitigation":  "string — action concrète"
    }
  ],

  "opportunities": [
    {
      "title":        "string",
      "description":  "string — opportunité concrète pour CETTE solution",
      "time_horizon": "short (0-6m) | medium (6-18m) | long (18m+)"
    }
  ],

  "kpis": {
    "addressable_market_local":  0,
    "internet_penetration_pct":  0,
    "mobile_penetration_per100": 0,
    "gdp_per_capita_usd":        0,
    "recommended_pricing_model": "string",
    "estimated_cac_usd":         "string",
    "market_maturity_score":     0
  },

  "go_no_go": {
    "verdict":      "GO | NO-GO | GO CONDITIONNEL",
    "confidence":   0,
    "main_reasons": ["string", "string", "string"],
    "conditions":   ["string — condition si GO CONDITIONNEL, sinon []"],
    "rationale":    "string — justification globale basée sur les données (une ligne)"
  },

  "recommendations": [
    {
      "title":       "string",
      "description": "string — action concrète et spécifique pour CETTE idée",
      "priority":    "HIGH | MEDIUM | LOW",
      "timeline":    "immédiat | 3 mois | 6 mois | 1 an",
      "rationale":   "string — basé sur quelle donnée précise"
    }
  ],

  "data_quality": {
    "sources_used":       ["serpapi", "tavily", "youtube", "newsapi", "reddit",
                           "google_trends", "tiktok", "worldbank", "regulatory"],
    "confidence_score":   0,
    "missing_data_notes": "string — données manquantes pour améliorer l'analyse (une ligne)"
  }
}"""


# ══════════════════════════════════════════════════════════════
# BUILD USER PROMPT
# ══════════════════════════════════════════════════════════════

def build_user_prompt(data: dict) -> str:
    """
    Construit le prompt utilisateur avec toutes les données collectées.
    L'idée complète est mise en avant pour contextualiser toute l'analyse.
    """

    idea = data.get("idea", {})

    # Résumé de l'idée mis en évidence au début du prompt
    idea_summary = f"""
PROBLÈME RÉSOLU  : {idea.get('problem', 'non défini')}
SOLUTION         : {idea.get('solution', 'non défini')}
PITCH            : {idea.get('pitch', 'non défini')}
CIBLE            : {idea.get('target', 'non défini')}
SECTEUR          : {idea.get('sector', 'non défini')}
PAYS             : {idea.get('country', 'Tunisie')} ({idea.get('country_code', 'TN')})
LANGUE MARCHÉ    : {idea.get('language', 'fr')}
""".strip()

    # Sérialisation de chaque section
    competitors_str     = json.dumps(data.get("raw_competitors", []),             ensure_ascii=False, indent=2)
    local_ratings_str   = json.dumps(data.get("local_ratings", []),               ensure_ascii=False, indent=2)
    tavily_comp_str     = json.dumps(data.get("tavily_competitor_summaries", []),  ensure_ascii=False, indent=2)
    organic_str         = json.dumps(data.get("organic_signals", []),              ensure_ascii=False, indent=2)
    youtube_str         = json.dumps(data.get("top_youtube_signals", []),          ensure_ascii=False, indent=2)
    news_str            = json.dumps(data.get("news_articles", []),                ensure_ascii=False, indent=2)
    funding_str         = json.dumps(data.get("funding_signals", []),              ensure_ascii=False, indent=2)
    regulatory_news_str = json.dumps(data.get("regulatory_signals", []),           ensure_ascii=False, indent=2)
    pain_str            = json.dumps(data.get("reddit_pain_points", []),           ensure_ascii=False, indent=2)
    mentions_str        = json.dumps(data.get("competitor_mentions", []),          ensure_ascii=False, indent=2)
    trends_str          = json.dumps(data.get("growth_trends", []),                ensure_ascii=False, indent=2)
    tiktok_str          = json.dumps(data.get("tiktok_signals", []),               ensure_ascii=False, indent=2)
    macro_str           = json.dumps(data.get("macro_context", {}),                ensure_ascii=False, indent=2)
    regulatory_str      = json.dumps(data.get("regulatory_data", []),              ensure_ascii=False, indent=2)

    # Calcul automatique du marché adressable si données disponibles
    macro = data.get("macro_context", {})
    pop = macro.get("population")
    inet = macro.get("internet_penetration")
    youth = macro.get("youth_population_pct")

    calc_hint = ""
    if pop and inet and youth:
        addressable = int(pop * (inet / 100) * (youth / 100))
        calc_hint = f"""
CALCUL PRÉ-FAIT (à utiliser dans kpis.addressable_market_local) :
population ({pop:,.0f}) × internet ({inet:.1f}%) × jeunes ({youth:.1f}%) = {addressable:,} personnes
→ kpis.addressable_market_local = {addressable}
"""

    return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IDÉE À ANALYSER — LIS ATTENTIVEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{idea_summary}
{calc_hint}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DONNÉES COLLECTÉES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

=== COMPETITORS — SerpAPI Google Search ===
{competitors_str}

=== COMPETITORS — SerpAPI Google Maps (ratings locaux) ===
{local_ratings_str}

=== COMPETITORS — Tavily (résumés enrichis) ===
{tavily_comp_str}

=== ORGANIC SIGNALS — SerpAPI ===
{organic_str}

=== YOUTUBE — Voice of Customer (titres + descriptions vidéos populaires) ===
{youtube_str}

=== TIKTOK — Signaux viraux secteur ===
{tiktok_str}

=== NEWS ARTICLES — NewsAPI + Newsdata ===
{news_str}

=== FUNDING SIGNALS ===
{funding_str}

=== REGULATORY NEWS — Actualités légales ===
{regulatory_news_str}

=== REDDIT PAIN POINTS — Via Tavily ===
{pain_str}

=== COMPETITOR MENTIONS — Reddit ===
{mentions_str}

=== GOOGLE TRENDS — Évolution demande ===
{trends_str}

=== MACRO CONTEXT — World Bank ===
{macro_str}

=== REGULATORY DATA — Cadre légal ===
{regulatory_str}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TASK — ANALYSE COMPLÈTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Analyse ces données et produis une analyse marché complète POUR L'IDÉE CI-DESSUS.

INSTRUCTIONS CRITIQUES :
1. Interprète TOUT en fonction du problem/solution/target/country de l'idée
   → Les concurrents sont directs si ils résolvent le MÊME problem pour la MÊME cible
   → Les pain points VOC doivent être liés au PROBLEM de l'idée
   → competitive_positioning : identifie le vrai gap marché depuis les faiblesses des concurrents + pain points VOC. Ex: si Apprentus a "frais élevés" + Reddit dit "trop cher" → main_gap = "absence de plateforme locale abordable"
   → market_entry_signal : croise Trends direction + funding signals + regulatory_outlook pour donner un timing clair.

2. TAM/SAM obligatoires :
   → tam_global_usd : estime avec les données disponibles, format "$X B"
   → sam_local_usd  : population × internet × youth × ARPU estimé
   → addressable_market_local : utilise le CALCUL PRÉ-FAIT ci-dessus si disponible

3. tiktok_signals doit être un tableau [] — jamais ""

4. go_no_go : verdict direct et justifié basé sur toutes les données

5. Langue : 100% français pour tout le contenu textuel

6. JSON compact : max 5 concurrents, max 4 risques, max 5 recommandations

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT — JSON STRICT (aucun texte avant/après)
Clés racine exactes : market_overview, competitors, swot, trends,
voice_of_customer, competitive_positioning, market_entry_signal, regulatory, risks, opportunities,
kpis, go_no_go, recommendations, data_quality

{OUTPUT_SCHEMA}
"""