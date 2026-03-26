import asyncio
import json
import sys
sys.path.insert(0, ".")

from agents.market_analysis import MarketAnalysisAgent

IDEA = {
    "short_pitch":          "Organisez vos cours automatiquement, gagnez du temps",
    "solution_description": "Application mobile qui génère automatiquement un emploi du temps personnalisé avec rappels et ajustements en temps réel",
    "target_users":         "Étudiants tunisiens (lycéens, universitaires)",
    "problem":              "Les étudiants peinent à gérer leurs cours, devoirs et activités — stress et mauvaise organisation",
    "country_code":         "TN",
    "language":             "fr",
}

async def main():
    agent = MarketAnalysisAgent()

    idea_str = f"{IDEA['short_pitch']}. {IDEA['solution_description']}. Cible : {IDEA['target_users']}. Problème : {IDEA['problem']}."

    print("Lancement analyse de marché...")
    print(f"Idée : {IDEA['short_pitch']}\n")

    result = await agent.run(
        idea=idea_str,
        country_code=IDEA["country_code"],
        language=IDEA["language"],
    )

    with open("market_analysis_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(json.dumps(result, ensure_ascii=False, indent=2))

asyncio.run(main())