import asyncio
import json
import sys

sys.path.insert(0, ".")

from agents.base_agent import PipelineState
from agents.market_analysis import MarketAnalysisAgent

# ══════════════════════════════════════════════════════
# IDÉES À TESTER — décommenter celle que tu veux
# ══════════════════════════════════════════════════════

IDEAS = {

    # "healthy_food": {
    #     "short_pitch": "Chips de légumes locaux healthy et vegan",
    #     "solution_description": "Production et vente de chips à base de légumes tunisiens (betterave, carotte, patate douce), sans additifs",
    #     "target_users": "Jeunes actifs, étudiants et sportifs en Tunisie",
    #     "problem": "Les snacks disponibles sont souvent gras, industriels et peu adaptés aux personnes cherchant une alimentation saine",
    #     "sector": "Healthy Food",
    #     "country_code": "TN",
    #     "language": "fr",
    # },

    # "edtech_app": {
    #     "short_pitch": "Application de gestion d'emploi du temps étudiant automatique",
    #     "solution_description": "App mobile qui organise automatiquement les cours, devoirs et examens des étudiants tunisiens",
    #     "target_users": "Étudiants universitaires en Tunisie 18-25 ans",
    #     "problem": "Les étudiants gèrent leur emploi du temps manuellement, oublient les deadlines et manquent de coordination",
    #     "sector": "EdTech",
    #     "country_code": "TN",
    #     "language": "fr",
    # },

    "food_delivery": {
        "short_pitch": "Livraison de repas healthy à domicile",
        "solution_description": "Plateforme de commande et livraison de repas sains préparés par des cuisiniers locaux certifiés",
        "target_users": "Professionnels et familles urbaines à Tunis",
        "problem": "Manque d'options de repas sains et rapides à livrer à domicile à Tunis",
        "sector": "FoodTech / Livraison",
        "country_code": "TN",
        "language": "fr",
    },

    # "ecommerce_mode": {
    #     "short_pitch": "Marketplace de vêtements locaux tunisiens en ligne",
    #     "solution_description": "Plateforme e-commerce dédiée aux créateurs et artisans tunisiens pour vendre leurs collections en ligne",
    #     "target_users": "Acheteurs 20-40 ans et créateurs de mode tunisiens",
    #     "problem": "Les artisans tunisiens n'ont pas de plateforme dédiée pour vendre leur production en ligne",
    #     "sector": "E-commerce / Mode",
    #     "country_code": "TN",
    #     "language": "fr",
    # },

    # "fintech": {
    #     "short_pitch": "Application de gestion budgétaire pour jeunes tunisiens",
    #     "solution_description": "App mobile de suivi des dépenses et épargne automatique adaptée au contexte bancaire tunisien",
    #     "target_users": "Jeunes actifs 22-35 ans en Tunisie",
    #     "problem": "Les jeunes tunisiens n'ont pas d'outil simple pour gérer leur budget et épargner",
    #     "sector": "FinTech",
    #     "country_code": "TN",
    #     "language": "fr",
    # },

    # "saas_rh": {
    #     "short_pitch": "Logiciel RH pour PME tunisiennes",
    #     "solution_description": "SaaS de gestion des congés, paie et recrutement adapté aux PME tunisiennes",
    #     "target_users": "DRH et dirigeants de PME en Tunisie",
    #     "problem": "Les PME tunisiennes gèrent les RH sur Excel, source d'erreurs et de perte de temps",
    #     "sector": "SaaS / RH",
    #     "country_code": "TN",
    #     "language": "fr",
    # },
}

# ══════════════════════════════════════════════════════
# CHOISIR L'IDÉE À TESTER ICI
# ══════════════════════════════════════════════════════
IDEA = IDEAS["food_delivery"]  # ← changer ici


def build_state_from_idea(idea: dict) -> PipelineState:
    state = PipelineState(
        idea_id="test-market-1",
        name=idea["short_pitch"],
        sector=idea.get("sector", "Secteur non défini"),
        description=f"{idea['solution_description']} Problème : {idea['problem']}",
        target_audience=idea["target_users"],
    )
    state.country = idea["country_code"]
    state.clarified_idea = {
        "short_pitch":          idea["short_pitch"],
        "solution_description": idea["solution_description"],
        "target_users":         idea["target_users"],
        "problem":              idea["problem"],
        "sector":               idea["sector"],
        "country_code":         idea["country_code"],
        "language":             idea["language"],
    }
    return state


async def main():
    agent = MarketAnalysisAgent()
    state = build_state_from_idea(IDEA)

    print("Lancement analyse de marché (orchestrateur + 3 sous-agents)...")
    print(f"Idée    : {IDEA['short_pitch']}")
    print(f"Secteur : {IDEA['sector']}")
    print(f"Pays    : {IDEA['country_code']}\n")

    state = await agent.run(state)

    report = state.market_analysis
    out_path = f"market_analysis_{IDEA['sector'].replace('/', '_').replace(' ', '_')}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n✅ Rapport sauvegardé : {out_path}")

    if state.errors:
        print("Erreurs pipeline :", state.errors)


if __name__ == "__main__":
    asyncio.run(main())