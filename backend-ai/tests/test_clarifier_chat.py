#!/usr/bin/env python3
# ══════════════════════════════════════════════════════════════
#  backend-ai/tests/test_clarifier_chat.py
#
#  Tu saisis tout à la main dans le terminal.
#
#  POUR LES CHAMPS LONGS (description, réponses) :
#    → Tape ligne par ligne
#    → Ligne vide + Entrée pour terminer
#
#  LANCER :
#    cd backend-ai
#    python tests/test_clarifier_chat.py
#
#  PRÉREQUIS .env :
#    GEMINI_API_KEY=ta_cle
#    LLM_MODEL=gemini-2.0-flash-exp
# ══════════════════════════════════════════════════════════════

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Couleurs ──────────────────────────────────────────────────
R      = "\033[0m"
B      = "\033[1m"
PURPLE = "\033[95m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
GRAY   = "\033[90m"
WHITE  = "\033[97m"


def sep():
    print(f"{GRAY}{'─' * 55}{R}")

def agent(t):
    print(f"\n{CYAN}{B}  Clarifier >{R} {t}\n")

def sys_msg(t):
    print(f"{YELLOW}  → {t}{R}")

def ok(t):
    print(f"{GREEN}  ✓ {t}{R}")

def fail(t):
    print(f"{RED}  ✗ {t}{R}")


def ask(label: str) -> str:
    """Saisie sur une seule ligne."""
    return input(f"{WHITE}{B}  Vous > {R}{label}").strip()


def ask_long(label: str) -> str:
    """
    Saisie multiligne — compatible Windows CMD et PowerShell.
    Tape ton texte ligne par ligne.
    Laisse une ligne VIDE et appuie sur Entrée pour terminer.
    """
    print(f"{WHITE}{B}  Vous > {R}{label}")
    print(f"{GRAY}  Tape ligne par ligne — ligne vide pour terminer :{R}")
    lines = []
    while True:
        try:
            line = input(f"{GRAY}  | {R}")
            if line.strip() == "":
                if lines:          # au moins une ligne saisie → on arrête
                    break
                else:              # rien encore → on continue à attendre
                    continue
            lines.append(line.strip())
        except EOFError:
            break
    return " ".join(lines)


def print_result(data: dict):
    sep()
    print(f"{GREEN}{B}  Résultat JSON{R}")
    sep()
    for key, label in [
        ("sector",               "Secteur"),
        ("target_users",         "Public cible"),
        ("problem",              "Problème"),
        ("solution_description", "Solution"),
        ("short_pitch",          "Pitch"),
    ]:
        val = data.get(key, "—")
        if val and len(val) > 80:
            val = val[:80] + "..."
        print(f"  {GRAY}{label:<18}{R}{val}")

    score = data.get("clarity_score", 0)
    bar   = "█" * (score // 10) + "░" * (10 - score // 10)
    color = GREEN if score >= 80 else YELLOW if score >= 55 else RED
    print(f"\n  {GRAY}{'Clarity score':<18}{R}{color}{score}/100  {bar}{R}")
    sep()


# ══════════════════════════════════════════════════════════════
#  CONVERSATION PRINCIPALE
# ══════════════════════════════════════════════════════════════

async def chat():
    from dotenv import load_dotenv
    load_dotenv()

    if not os.getenv("GEMINI_API_KEY"):
        fail("GEMINI_API_KEY manquante dans backend-ai/.env")
        sys.exit(1)

    from agents.base_agent import PipelineState
    from agents.idea_clarifier import IdeaClarifierAgent

    # ── Intro ─────────────────────────────────────────────────
    print(f"\n{PURPLE}{B}  BrandAI — Idea Clarifier{R}")
    print(f"{GRAY}  Saisis ton idée ci-dessous.{R}\n")
    sep()

    # ── Saisie des champs ─────────────────────────────────────
    print()
    name        = ask("Nom du projet   : ")
    sector      = ask("Secteur         : ")
    audience    = ask("Public cible    : ")
    description = ask_long("Description     :")

    if not name or not sector or not description:
        fail("Nom, secteur et description sont obligatoires.")
        sys.exit(1)

    # ── Confirmation ──────────────────────────────────────────
    print()
    sep()
    print(f"  {GRAY}Nom         {R}: {WHITE}{name}{R}")
    print(f"  {GRAY}Secteur     {R}: {WHITE}{sector}{R}")
    print(f"  {GRAY}Public      {R}: {WHITE}{audience or '—'}{R}")
    desc_preview = description[:100] + ("..." if len(description) > 100 else "")
    print(f"  {GRAY}Description {R}: {WHITE}{desc_preview}{R}")
    sep()

    state = PipelineState(
        idea_id         = 1,
        name            = name,
        sector          = sector,
        description     = description,
        target_audience = audience,
    )

    agent_instance = IdeaClarifierAgent()

    # ══════════════════════════════════════════════════════════
    #  APPEL LLM 1 — Sécurité
    # ══════════════════════════════════════════════════════════
    print()
    sys_msg("Appel LLM 1 — vérification sécurité...")

    safety = await agent_instance.check_safety(state)

    if not safety["safe"]:
        print()
        fail("Projet refusé — pipeline arrêté.")
        agent(safety.get("refusal_message", "Ce projet ne peut pas être traité."))
        sys_msg(f"Catégorie   : {safety.get('reason_category')}")
        sys_msg("Appel LLM 2 : non lancé.")
        return

    ok("safe: true — on continue")

    # ══════════════════════════════════════════════════════════
    #  APPEL LLM 2a — Évaluation dimensions
    # ══════════════════════════════════════════════════════════
    print()
    sys_msg("Appel LLM 2a — analyse de la description...")

    richness  = await agent_instance._evaluate_richness(state)
    questions = agent_instance.build_questions(richness)

    ok(f"has_problem={richness['has_problem']}  "
       f"has_target={richness['has_target']}  "
       f"has_solution={richness['has_solution']}")

    # ══════════════════════════════════════════════════════════
    #  QUESTIONS si dimensions manquantes
    # ══════════════════════════════════════════════════════════
    answers = []

    if questions:
        print()
        agent(
            f"J'ai {len(questions)} question{'s' if len(questions) > 1 else ''} "
            f"pour mieux comprendre votre projet."
        )
        for i, question in enumerate(questions):
            print(f"  {CYAN}{B}Q{i+1}.{R} {question}")
            answer = ask_long("")
            answers.append(answer)
            print()
    else:
        print()
        agent("Description complète — aucune question nécessaire.")

    # ══════════════════════════════════════════════════════════
    #  APPEL LLM 2b — Génération JSON
    # ══════════════════════════════════════════════════════════
    print()
    sys_msg("Appel LLM 2b — génération du JSON structuré...")

    clarified = await agent_instance.generate_clarified_idea(
        state,
        user_answers=answers if answers else None,
    )

    ok("JSON généré")

    print()
    agent("Voici la description structurée de votre projet :")
    print_result(clarified)

    state.clarified_idea = clarified
    state.clarity_score  = clarified.get("clarity_score", 0)
    score = state.clarity_score

    if score >= 80:
        agent("Description très claire — pipeline prêt à démarrer.")
    elif score >= 55:
        agent("Description acceptable — l'Idea Enhancer complétera les détails.")
    else:
        agent("Description encore vague — l'Idea Enhancer travaillera avec des hypothèses.")

    print(f"{GRAY}  Prochain agent : Idea Enhancer{R}\n")


if __name__ == "__main__":
    try:
        asyncio.run(chat())
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}  Session interrompue.{R}\n")