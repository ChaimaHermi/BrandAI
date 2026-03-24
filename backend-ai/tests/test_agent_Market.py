#!/usr/bin/env python3
# ══════════════════════════════════════════════════════════════
#  run_market.py
#  Script CLI pour tester le Market Analysis Agent
#
#  Usage :
#    python run_market.py                        # utilise l'idée exemple
#    python run_market.py idea.json              # charge depuis un fichier
#    python run_market.py '{"sector": "EdTech"}' # JSON inline
# ══════════════════════════════════════════════════════════════

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# Ensure local absolute imports (agents, tools, llm, ...) work
# even when script is launched from repo root.
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from agents.base_agent import PipelineState
from agents.market_analysis import MarketAnalysisAgent
# ── Logging lisible dans le terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)

# ══════════════════════════════════════════════════════════════
# IDÉE EXEMPLE (utilisée si aucun argument)
# ══════════════════════════════════════════════════════════════

DEFAULT_IDEA = {
    "problem":  "Les étudiants tunisiens n'ont pas accès à du tutorat de qualité abordable",
    "solution": "Plateforme de mise en relation étudiants / tuteurs avec sessions vidéo",
    "pitch":    "Airbnb du tutorat en Tunisie — tuteurs vérifiés, paiement sécurisé, scheduling auto",
    "target":   "Étudiants universitaires 18-26 ans, Tunisie",
    "sector":   "EdTech",
}

# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

async def main():

    # ── Chargement de l'idée
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        try:
            # Argument inline JSON
            if arg.strip().startswith("{"):
                idea = json.loads(arg)
            # Fichier JSON
            else:
                with open(arg, "r", encoding="utf-8") as f:
                    idea = json.load(f)
        except Exception as e:
            print(f"[ERROR] Erreur chargement idee : {e}")
            sys.exit(1)
    else:
        idea = DEFAULT_IDEA
        print("[INFO] Aucun argument - utilisation de l'idee exemple (EdTech Tunisie)\n")

    print("=" * 60)
    print("  MARKET ANALYSIS AGENT")
    print("=" * 60)
    print(f"  Secteur  : {idea.get('sector', '?')}")
    print(f"  Cible    : {idea.get('target', '?')}")
    print(f"  Problème : {idea.get('problem', '?')[:60]}...")
    print("=" * 60 + "\n")

    # ── Création du state
    state = PipelineState(
        idea_id=f"test_{int(time.time())}",
        name=idea.get("sector", "test"),
        sector=idea.get("sector", ""),
        description=idea.get("pitch", idea.get("problem", "")),
        target_audience=idea.get("target", ""),
    )
    state.clarified_idea = idea

    # ── Lancement agent
    agent = MarketAnalysisAgent()

    start = time.time()
    state = await agent.run(state)
    elapsed = round(time.time() - start, 1)

    # ── Résultat
    print("\n" + "=" * 60)

    if state.status == "error":
        print(f"[ERROR] ERREUR apres {elapsed}s")
        for err in state.errors:
            print(f"   -> {err}")
        sys.exit(1)

    print(f"[OK] SUCCES en {elapsed}s")
    print("=" * 60)

    # Aperçu rapide
    ma = state.market_analysis
    if ma:
        overview = ma.get("market_overview", {})
        print(f"\n[Market] Secteur      : {overview.get('sector', '?')}")
        print(f"   TAM Global   : {overview.get('tam_global_usd', '?')}")
        print(f"   SAM Local    : {overview.get('sam_local_usd', '?')}")
        print(f"   Maturité     : {overview.get('market_maturity_label', '?')} ({overview.get('market_maturity_score', '?')}/100)")
        print(f"   Timing       : {overview.get('timing_signal', '?')[:80]}...")

        competitors = ma.get("competitors", [])
        print(f"\n[Competition] Concurrents  : {len(competitors)} identifies")
        for c in competitors[:3]:
            print(f"   - {c.get('name', '?')} - threat={c.get('threat_score', '?')}/100")

        dq = ma.get("data_quality", {})
        print(f"\n[DataQuality] Confiance    : {dq.get('confidence_score', '?')}/100")
        print(f"   Sources      : {', '.join(dq.get('sources_used', []))}")

    print("\n[Files] Fichiers generes :")
    print("   - market_raw_data.json   (donnees brutes des APIs)")
    print("   - market_analysis.json   (analyse finale structuree)")
    print()


if __name__ == "__main__":
    asyncio.run(main())