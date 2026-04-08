"""
tests/test_keyword_extractor.py
================================
Test standalone du KeywordExtractor.

Usage :
    cd backend-ai
    python tests/test_keyword_extractor.py

Ce test vérifie :
  1. Le LLM retourne un JSON valide
  2. Le KeywordBundle est bien rempli
  3. Chaque compartiment contient des données réelles
  4. Les accesseurs for_X() retournent les bonnes clés
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── Path setup ────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agents.market_analysis.orchestrator.keyword_extractor import (
    KeywordBundle,
    KeywordExtractor,
)

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("test.keyword_extractor")

# ── IDEA de test ──────────────────────────────────────────────
IDEA = {
    "short_pitch": "Online second-hand clothing marketplace Tunisia",
    "solution_description": "Mobile and web platform where users in Tunisia create a virtual wardrobe, sell second-hand clothes, and buy directly from other users locally",
    "target_users": "Young Tunisian consumers who want affordable fashion and resell their clothes easily",
    "problem": "Second-hand clothing resale in Tunisia is fragmented, informal, and lacks a trusted digital platform",
    "sector": "E-commerce / Marketplace",
    "country": "Tunisia",
    "country_code": "TN",
    "language": "en",
}
# ═══════════════════════════════════════════════════════════════
# TEST PRINCIPAL
# ═══════════════════════════════════════════════════════════════

async def test_keyword_extractor():

    print("\n" + "="*60)
    print("TEST - KeywordExtractor")
    print("="*60)
    print(f"Idee    : {IDEA['short_pitch']}")
    print(f"Secteur : {IDEA['sector']}")
    print(f"Pays    : {IDEA['country_code']}")
    print("="*60 + "\n")

    # ── Extraction ────────────────────────────────────────────
    extractor = KeywordExtractor()

    print("... Appel LLM en cours...\n")
    bundle = await extractor.extract(IDEA)

    # ── Résultat brut ─────────────────────────────────────────
    print("="*60)
    print("KEYWORD BUNDLE - RESULTAT COMPLET")
    print("="*60)
    print(json.dumps(bundle.to_dict(), indent=2, ensure_ascii=False))

    # ── Accesseurs par agent ──────────────────────────────────
    print("\n" + "="*60)
    print("CE QUE CHAQUE AGENT RECOIT")
    print("="*60)

    print("\n[market_sizing_agent] recoit :")
    print(json.dumps(bundle.for_market_sizing(), indent=2, ensure_ascii=False))

    print("\n[competitor_agent] recoit :")
    print(json.dumps(bundle.for_competitor(), indent=2, ensure_ascii=False))

    print("\n[voc_agent] recoit :")
    print(json.dumps(bundle.for_voc(), indent=2, ensure_ascii=False))

    print("\n[trends_agent] recoit :")
    print(json.dumps(bundle.for_trends(), indent=2, ensure_ascii=False))

    # ── Assertions ────────────────────────────────────────────
    print("\n" + "="*60)
    print("VALIDATIONS")
    print("="*60)

    results = []

    def check(name: str, condition: bool):
        icon = "[OK]" if condition else "[X]"
        print(f"  {icon} {name}")
        results.append((name, condition))

    check("bundle non vide",                          not bundle.is_empty())
    check("primary_keywords rempli",                  len(bundle.primary_keywords) > 0)
    check("primary_keywords max 6",                   len(bundle.primary_keywords) <= 6)
    check("market_keywords rempli",                      len(bundle.market_keywords) > 0)
    check("market_keywords max 6",                       len(bundle.market_keywords) <= 6)
    check("competitor_queries rempli",                 len(bundle.competitor_queries) > 0)
    check("competitor_queries max 10",                  len(bundle.competitor_queries) <= 10)
    check("voc_keywords rempli",                      len(bundle.voc_keywords) > 0)
    check("voc_keywords max 6",                       len(bundle.voc_keywords) <= 6)
    check("trend_keywords rempli",                    len(bundle.trend_keywords) > 0)
    check("trend_keywords max 5",                     len(bundle.trend_keywords) <= 5)
    check("for_market_sizing a primary_keywords",     "primary_keywords" in bundle.for_market_sizing())
    check("for_market_sizing a market_keywords",      "market_keywords"  in bundle.for_market_sizing())
    check("for_market_sizing a trend_keywords",       "trend_keywords"   in bundle.for_market_sizing())
    check("for_competitor est une liste",             isinstance(bundle.for_competitor(), list))
    check("for_voc a voc_keywords",                  "voc_keywords"     in bundle.for_voc())
    check("for_trends a primary_keywords",            "primary_keywords" in bundle.for_trends())
    check("tous les keywords sont des strings",       all(
        isinstance(k, str)
        for lst in [
            bundle.primary_keywords,
            bundle.market_keywords,
            bundle.competitor_queries,
            bundle.voc_keywords,
            bundle.trend_keywords,
        ]
        for k in lst
    ))
    check("aucun keyword vide",                       all(
        k.strip()
        for lst in [
            bundle.primary_keywords,
            bundle.market_keywords,
            bundle.competitor_queries,
            bundle.voc_keywords,
            bundle.trend_keywords,
        ]
        for k in lst
    ))

    # ── Résumé ────────────────────────────────────────────────
    passed = sum(1 for _, ok in results if ok)
    total  = len(results)

    print(f"\n{'='*60}")
    print(f"RESULTAT : {passed}/{total} validations passees")

    if passed == total:
        print("OK KeywordExtractor fonctionne correctement")
    else:
        failed = [name for name, ok in results if not ok]
        print(f"ECHECS : {failed}")

    print("="*60 + "\n")

    return passed == total


# ═══════════════════════════════════════════════════════════════
# ENTRÉE
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    success = asyncio.run(test_keyword_extractor())
    sys.exit(0 if success else 1)