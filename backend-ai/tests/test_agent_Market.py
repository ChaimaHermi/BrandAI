#!/usr/bin/env python3
# ══════════════════════════════════════════════════════════════
#  run_market.py  —  BrandAI
#  Script de test complet Market Analysis Agent
#
#  Usage :
#    python run_market.py                        # idée exemple EdTech
#    python run_market.py --idea idea.json       # depuis fichier JSON
#    python run_market.py --sector "FinTech"     # secteur rapide
#    python run_market.py --test-apis            # teste les APIs uniquement
#    python run_market.py --verbose              # affiche raw data aussi
# ══════════════════════════════════════════════════════════════

import asyncio
import json
import logging
import sys
import time
import argparse
from pathlib import Path

# Import path fix
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv()

from agents.base_agent import PipelineState
from agents.market_analysis import MarketAnalysisAgent
from utils.market_utils import build_queries
from tools.market_tools import (
    fetch_serpapi,
    fetch_tavily_competitor,
    fetch_youtube,
    fetch_news,
    fetch_reddit,
    fetch_trends,
    fetch_worldbank,
    fetch_regulatory,
)

# ── Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("run_market")


# ══════════════════════════════════════════════════════════════
# IDÉES DE TEST
# ══════════════════════════════════════════════════════════════

TEST_IDEAS = {
    "edtech": {
        "problem":  "Les étudiants tunisiens n'ont pas accès à du tutorat de qualité abordable",
        "solution": "Plateforme de mise en relation étudiants / tuteurs avec sessions vidéo",
        "pitch":    "Airbnb du tutorat en Tunisie — tuteurs vérifiés, paiement sécurisé",
        "target":   "Étudiants universitaires 18-26 ans, Tunisie",
        "sector":   "EdTech",
        "country":  "Tunisie",
        "country_code": "TN",
        "language": "fr",
    },
    # "fintech": {
    #     "problem":  "Les PME tunisiennes ont du mal à accéder au financement bancaire",
    #     "solution": "Plateforme de microcrédit peer-to-peer pour PME",
    #     "pitch":    "Financement participatif pour PME Tunisie — sans banque",
    #     "target":   "PME 5-50 employés, Tunisie et Maghreb",
    #     "sector":   "FinTech",
    #     "country":  "Tunisie",
    #     "country_code": "TN",
    #     "language": "fr",
    # },
    # "healthtech": {
    #     "problem":  "Difficile de trouver un médecin disponible rapidement en Tunisie",
    #     "solution": "Application de téléconsultation médicale avec IA de triage",
    #     "pitch":    "Doctolib de la Tunisie — consultation vidéo en 15 min",
    #     "target":   "Patients 25-55 ans, zones urbaines Tunisie",
    #     "sector":   "HealthTech",
    #     "country":  "Tunisie",
    #     "country_code": "TN",
    #     "language": "fr",
    # },
}


# ══════════════════════════════════════════════════════════════
# TEST APIS SEULEMENT
# ══════════════════════════════════════════════════════════════

async def test_apis_only(idea: dict):
    """Teste chaque API individuellement sans appel LLM."""

    print("\n" + "═" * 60)
    print("  TEST APIs — sans LLM")
    print("═" * 60)

    # Génère les queries via LLM
    print("\n[1/9] Génération queries via LLM...")
    start = time.time()
    queries = await build_queries(
        problem=idea.get("problem", ""),
        target=idea.get("target", ""),
        sector=idea.get("sector", ""),
        solution=idea.get("solution", ""),
        country=idea.get("country", "Tunisie"),
        country_code=idea.get("country_code", "TN"),
        language=idea.get("language", "fr"),
    )
    print(f"   ✓ Queries générées en {round(time.time()-start, 1)}s")
    print(f"   serpapi_local  : {queries.get('serpapi_local', [])}")
    print(f"   serpapi_trends : {queries.get('serpapi_trends', [])}")
    print(f"   tavily_voc     : {queries.get('tavily_voc', [])[:1]}")

    # Test chaque tool
    tools = [
        ("SerpAPI Search",        fetch_serpapi,           queries),
        ("Tavily Competitor",     fetch_tavily_competitor, queries),
        ("YouTube",               fetch_youtube,           queries),
        ("NewsAPI + Newsdata",    fetch_news,              queries),
        ("Reddit via Tavily",     fetch_reddit,            queries),
        ("Google Trends + TikTok",fetch_trends,            queries),
        ("World Bank",            fetch_worldbank,         idea.get("country_code", "TN")),
        ("Regulatory",            fetch_regulatory,        queries),
    ]

    results = {}
    for i, (name, func, arg) in enumerate(tools, 2):
        print(f"\n[{i}/9] {name}...")
        start = time.time()
        try:
            if name == "World Bank":
                result = await func(arg)
            else:
                result = await func(arg)
            elapsed = round(time.time() - start, 1)

            # Résumé par tool
            if name == "SerpAPI Search":
                n_comp = len(result.get("competitors", []))
                n_maps = len(result.get("local_ratings", []))
                print(f"   ✓ {elapsed}s — {n_comp} concurrents, {n_maps} ratings Maps")

            elif name == "Tavily Competitor":
                n = len(result.get("competitor_summaries", []))
                src = result.get("source", "?")
                print(f"   ✓ {elapsed}s — {n} résumés [{src}]")

            elif name == "YouTube":
                n = len(result.get("trending_videos", []))
                if n > 0:
                    print(f"   ✓ {elapsed}s — {n} vidéos | ex: {result['trending_videos'][0].get('title','?')[:50]}")
                else:
                    print(f"   ⚠ {elapsed}s — 0 vidéos")

            elif name == "NewsAPI + Newsdata":
                n = len(result.get("articles", []))
                nf = len(result.get("funding_signals", []))
                print(f"   ✓ {elapsed}s — {n} articles, {nf} funding signals")

            elif name == "Reddit via Tavily":
                n = len(result.get("posts", []))
                np = len(result.get("pain_points", []))
                print(f"   ✓ {elapsed}s — {n} posts, {np} pain points")
                if result.get("pain_points"):
                    print(f"   Pain points: {result['pain_points'][:2]}")

            elif name == "Google Trends + TikTok":
                nt = len(result.get("trends", []))
                ntk = len(result.get("tiktok_signals", []))
                print(f"   ✓ {elapsed}s — {nt} trends, {ntk} TikTok signals")

            elif name == "World Bank":
                gdp = result.get("gdp_per_capita")
                inet = result.get("internet_penetration")
                print(f"   ✓ {elapsed}s — GDP/cap: ${gdp:.0f} | Internet: {inet:.1f}%" if gdp and inet else f"   ✓ {elapsed}s — {result}")

            elif name == "Regulatory":
                n = len(result.get("regulatory_data", []))
                print(f"   ✓ {elapsed}s — {n} résultats regulatory")

            results[name] = result

        except Exception as e:
            print(f"   ✗ ERREUR: {e}")
            results[name] = {}

    # Sauvegarde raw data
    with open("test_raw_data.json", "w", encoding="utf-8") as f:
        json.dump({"queries": queries, "results": results}, f, ensure_ascii=False, indent=2)
    print("\n✓ Raw data sauvegardée → test_raw_data.json")

    return queries, results


# ══════════════════════════════════════════════════════════════
# TEST COMPLET (APIs + LLM)
# ══════════════════════════════════════════════════════════════

async def test_full_agent(idea: dict, verbose: bool = False):
    """Test complet — APIs + LLM analyse."""

    print("\n" + "═" * 60)
    print("  MARKET ANALYSIS AGENT — TEST COMPLET")
    print("═" * 60)
    print(f"  Secteur  : {idea.get('sector', '?')}")
    print(f"  Pays     : {idea.get('country', '?')}")
    print(f"  Cible    : {idea.get('target', '?')}")
    print(f"  Problème : {idea.get('problem', '')[:70]}...")
    print("═" * 60 + "\n")

    state = PipelineState(
        idea_id=f"test_{int(time.time())}",
        name=idea.get("sector", "test"),
        sector=idea.get("sector", ""),
        description=idea.get("pitch", idea.get("problem", "")),
        target_audience=idea.get("target", ""),
    )
    state.clarified_idea = idea

    agent = MarketAnalysisAgent()
    start = time.time()

    print("[...] Lancement pipeline complet...")
    state = await agent.run(state)
    elapsed = round(time.time() - start, 1)

    print("\n" + "═" * 60)

    if state.status == "error":
        print(f"[✗] ERREUR après {elapsed}s")
        for err in state.errors:
            print(f"   → {err}")
        return None

    print(f"[✓] SUCCÈS en {elapsed}s")
    print("═" * 60)

    ma = state.market_analysis
    if not ma:
        print("[⚠] market_analysis vide")
        return None

    # ── Affichage résultats ───────────────────────────────────
    _print_results(ma, verbose)

    # Sauvegarde
    with open("market_analysis_test.json", "w", encoding="utf-8") as f:
        json.dump(ma, f, ensure_ascii=False, indent=2)
    print("\n[Files] market_analysis_test.json sauvegardé")

    return ma


def _print_results(ma: dict, verbose: bool = False):
    """Affiche les résultats de façon lisible."""

    # Market Overview
    ov = ma.get("market_overview", {})
    print(f"\n{'─'*40}")
    print("MARKET OVERVIEW")
    print(f"{'─'*40}")
    print(f"  Secteur    : {ov.get('sector', '?')}")
    print(f"  TAM Global : {ov.get('tam_global_usd', '?')}")
    print(f"  SAM Local  : {ov.get('sam_local_usd', '?')}")
    print(f"  CAGR       : {ov.get('tam_cagr_pct', '?')}%")
    print(f"  Maturité   : {ov.get('market_maturity_label', '?')} ({ov.get('market_maturity_score', '?')}/100)")
    print(f"  Timing     : {str(ov.get('timing_signal', '?'))[:80]}")

    # Competitors
    comps = ma.get("competitors", [])
    print(f"\n{'─'*40}")
    print(f"CONCURRENTS ({len(comps)} identifiés)")
    print(f"{'─'*40}")
    for c in comps[:4]:
        print(f"  [{c.get('threat_score', '?')}/100] {c.get('name', '?')} — {c.get('type', '?')}")
        if verbose and c.get("weaknesses"):
            print(f"    Faiblesses: {c['weaknesses'][:2]}")

    # SWOT
    swot = ma.get("swot", {})
    print(f"\n{'─'*40}")
    print("SWOT")
    print(f"{'─'*40}")
    for key, label in [("strengths","S"), ("weaknesses","W"), ("opportunities","O"), ("threats","T")]:
        items = swot.get(key, [])[:2]
        for item in items:
            print(f"  [{label}] {str(item)[:70]}")

    # VOC
    voc = ma.get("voice_of_customer", {})
    print(f"\n{'─'*40}")
    print("VOICE OF CUSTOMER")
    print(f"{'─'*40}")
    for pp in voc.get("top_pain_points", [])[:3]:
        print(f"  Pain: {str(pp)[:70]}")
    for tk in voc.get("tiktok_signals", [])[:2]:
        print(f"  TikTok: {str(tk)[:70]}")

    # Competitive positioning
    cp = ma.get("competitive_positioning", {})
    print(f"\n{'─'*40}")
    print("COMPETITIVE POSITIONING")
    print(f"{'─'*40}")
    print(f"  Gap        : {str(cp.get('main_gap', '?'))[:80]}")
    print(f"  Diff       : {str(cp.get('differentiation_angle', '?'))[:80]}")
    print(f"  Menace     : {cp.get('threat_level', '?')}")

    # Market entry signal
    mes = ma.get("market_entry_signal", {})
    print(f"\n{'─'*40}")
    print("MARKET ENTRY SIGNAL")
    print(f"{'─'*40}")
    print(f"  Timing     : {mes.get('timing', '?')}")
    print(f"  Action 1   : {str(mes.get('first_action', '?'))[:80]}")

    # Go/No-Go
    gng = ma.get("go_no_go", {})
    verdict = gng.get("verdict", "?")
    confidence = gng.get("confidence", 0)
    emoji = "✅" if verdict == "GO" else "⚠️" if "CONDITIONNEL" in str(verdict) else "❌"
    print(f"\n{'─'*40}")
    print(f"GO/NO-GO : {emoji} {verdict} (confiance: {confidence}%)")
    print(f"{'─'*40}")
    for r in gng.get("main_reasons", [])[:3]:
        print(f"  → {str(r)[:80]}")
    if gng.get("conditions"):
        for c in gng.get("conditions", [])[:2]:
            if c:
                print(f"  Condition: {str(c)[:80]}")

    # Recommendations
    recs = ma.get("recommendations", [])
    print(f"\n{'─'*40}")
    print(f"RECOMMANDATIONS ({len(recs)})")
    print(f"{'─'*40}")
    for rec in recs[:3]:
        p = rec.get("priority", "?")
        print(f"  [{p}] {rec.get('title', '?')}")
        if verbose:
            print(f"       {str(rec.get('description',''))[:80]}")

    # Data Quality
    dq = ma.get("data_quality", {})
    print(f"\n{'─'*40}")
    print("DATA QUALITY")
    print(f"{'─'*40}")
    print(f"  Confiance : {dq.get('confidence_score', '?')}/100")
    print(f"  Sources   : {', '.join(dq.get('sources_used', []))}")
    if dq.get("missing_data_notes"):
        print(f"  Manquant  : {str(dq['missing_data_notes'])[:80]}")


# ══════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════

def parse_args():
    parser = argparse.ArgumentParser(description="Test Market Analysis Agent")
    parser.add_argument("--idea",      help="Fichier JSON de l'idée")
    parser.add_argument("--sector",    help="Secteur prédéfini: edtech|fintech|healthtech", default="edtech")
    parser.add_argument("--test-apis", action="store_true", help="Teste les APIs seulement (sans LLM analyse)")
    parser.add_argument("--verbose",   action="store_true", help="Affiche plus de détails")
    parser.add_argument("--country",   help="Code pays ISO2 (ex: TN, MA, DZ)", default="TN")
    return parser.parse_args()


async def main():
    args = parse_args()

    # ── Chargement idée ───────────────────────────────────────
    if args.idea:
        with open(args.idea, encoding="utf-8") as f:
            idea = json.load(f)
        print(f"[INFO] Idée chargée depuis {args.idea}")
    else:
        sector_key = args.sector.lower()
        idea = TEST_IDEAS.get(sector_key, TEST_IDEAS["edtech"])
        if args.country != "TN":
            idea["country_code"] = args.country
        print(f"[INFO] Idée exemple : {sector_key.upper()}")

    # ── Mode test ─────────────────────────────────────────────
    if args.test_apis:
        await test_apis_only(idea)
    else:
        await test_full_agent(idea, verbose=args.verbose)


if __name__ == "__main__":
    asyncio.run(main())