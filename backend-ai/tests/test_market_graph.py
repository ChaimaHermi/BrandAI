import asyncio
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pipeline.market_graph import build_market_graph


SAMPLE_IDEA = {
    "short_pitch": "Marketplace de vêtements d'occasion en ligne",
    "solution_description": "Plateforme pour acheter et vendre des vêtements de seconde main",
    "target_users": "Consommateurs soucieux du budget et de l'environnement",
    "problem": "Difficulté à trouver une plateforme fiable pour le resale en Tunisie",
    "sector": "E-commerce / Marketplace",
    "country": "Tunisia",
    "country_code": "TN",
    "language": "fr",
}


async def run_test():
    graph = build_market_graph()
    initial = {
        "idea_id": "TEST-MARKET-GRAPH-001",
        "clarified_idea": SAMPLE_IDEA,
        "market_analysis": {},
    }
    final = await graph.ainvoke(initial)
    print("\n====================")
    print("FINAL STATE")
    print(json.dumps(final, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    asyncio.run(run_test())
