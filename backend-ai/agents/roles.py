 
# ══════════════════════════════════════════
#   backend-ai/agents/roles.py
#   Constantes des rôles et labels de tous les agents BrandAI
#   Utilisé par l'orchestrateur LangGraph et le WebSocket XAI
# ══════════════════════════════════════════

# ── Noms des nœuds LangGraph ──────────────────────────────────
# Ces noms correspondent EXACTEMENT aux nœuds déclarés dans orchestrator.py

AGENT_CLARIFIER         = "idea_clarifier"
AGENT_ENHANCER          = "idea_enhancer"
AGENT_MARKET            = "market_analysis"
AGENT_STRATEGY          = "marketing_strategy"
AGENT_BRAND             = "brand_identity"
AGENT_CONTENT           = "content_creator"
AGENT_WEBSITE           = "website_builder"
AGENT_OPTIMIZER         = "optimizer"

# ── Labels affichés dans l'UI / WebSocket XAI ────────────────

AGENT_LABELS: dict[str, str] = {
    AGENT_CLARIFIER: "Idea Clarifier",
    AGENT_ENHANCER:  "Idea Enhancer",
    AGENT_MARKET:    "Market Analysis",
    AGENT_STRATEGY:  "Marketing Strategy",
    AGENT_BRAND:     "Brand Identity",
    AGENT_CONTENT:   "Content Creator",
    AGENT_WEBSITE:   "Website Builder",
    AGENT_OPTIMIZER: "Optimizer",
}

# ── Ensemble des nœuds connus (pour filtrer les events LangGraph) ──

PIPELINE_NODES: set[str] = set(AGENT_LABELS.keys())

# ── Ordre du pipeline par phase ───────────────────────────────

PHASE_1 = [AGENT_CLARIFIER, AGENT_ENHANCER, AGENT_MARKET, AGENT_STRATEGY]
PHASE_2 = [AGENT_BRAND, AGENT_CONTENT]
PHASE_3 = [AGENT_WEBSITE, AGENT_OPTIMIZER]