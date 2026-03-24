# ══════════════════════════════════════════════════════════════
#  market_utils.py
#  Génère des queries adaptées par outil à partir de l'idée
# ══════════════════════════════════════════════════════════════


def build_queries(problem: str, target: str, sector: str = "", solution: str = "") -> dict:
    """
    Génère des queries ciblées pour chaque outil.

    Args:
        problem  : le problème résolu (ex: "étudiants n'ont pas accès au tutorat")
        target   : la cible (ex: "étudiants universitaires Tunisie")
        sector   : le secteur (ex: "EdTech")
        solution : la solution proposée (ex: "plateforme de tutorat en ligne")

    Returns:
        dict avec clés : competitors, trends, youtube, reddit, google_trends, news
    """

    # ── Nettoyage basique
    problem  = problem.strip()
    target   = target.strip()
    sector   = sector.strip()
    solution = solution.strip()

    # ── Contexte court pour les queries
    ctx = sector or problem[:40]

    queries = {

        # SerpAPI — trouver les concurrents directs + signaux de marché
        "competitors": [
            f"{ctx} platform competitors",
            f"best {ctx} startups 2024",
            f"{ctx} market leaders",
            f"{solution} alternatives" if solution else f"{ctx} tools alternatives",
            f"{ctx} {target} solution",
        ],

        # SerpAPI — signaux de tendances marché
        "trends": [
            f"{ctx} market size 2024",
            f"{ctx} growth trends",
            f"{ctx} industry report",
            f"{ctx} investment funding 2024",
        ],

        # YouTube — comportement utilisateur + évangélisation
        "youtube": [
            f"{ctx} tutorial",
            f"{ctx} review 2024",
            f"how to {problem[:30]}",
            f"{ctx} {target}",
        ],

        # Reddit — pain points + frustrations utilisateurs
        "reddit": [
            f"{problem[:60]}",
            f"{ctx} frustration",
            f"{ctx} problems users",
            f"alternatives to {ctx}",
        ],

        # Google Trends — évolution de la demande
        "google_trends": [
            ctx,
            solution[:40] if solution else ctx,
            f"{ctx} online",
            target[:30],
        ],

        # NewsAPI — actualités, funding, régulation
        "news": [
            f"{ctx} startup funding",
            f"{ctx} market news",
            f"{ctx} regulation",
        ],
    }

    return queries