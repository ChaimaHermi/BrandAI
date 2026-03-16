# ══════════════════════════════════════════════════════════════
#  backend-ai/agents/idea_clarifier.py
#  Agent 0 — Idea Clarifier
#
#  RÔLE UNIQUE : Comprendre ce que l'utilisateur veut faire.
#
#  FLUX — 2 appels LLM séquentiels :
#
#    Appel 1 : check_safety()
#      → Prompt court, focalisé sur l'intention réelle
#      → safe: false  → STOP immédiat, appel 2 jamais lancé
#      → safe: true   → on continue
#
#    Appel 2 : generate_clarified_idea()
#      → Seulement si l'appel 1 dit safe: true
#      → Pose 0-3 questions si description vague
#      → Produit le JSON de clarification
#
#  CE QUE CET AGENT NE FAIT PAS :
#    - Générer un nom de marque   → Brand Identity Agent
#    - Enrichir stratégiquement   → Idea Enhancer Agent
#    - Analyser la concurrence    → Market Analysis Agent
#    - Proposer un business model → Idea Enhancer Agent
#
#  OUTPUT JSON (envoyé à l'Idea Enhancer) :
#    {
#      "sector":               str,
#      "target_users":         str,
#      "problem":              str,
#      "solution_description": str,
#      "short_pitch":          str,
#      "clarity_score":        int (0-100)
#    }
# ══════════════════════════════════════════════════════════════

from agents.base_agent import BaseAgent, PipelineState
from guardrails.safety_checks import get_refusal_message
from tools.idea_tools import build_idea_summary, validate_idea_input


# ══════════════════════════════════════════════════════════════
#  PROMPTS — constantes de module
#  Chaque prompt a UN seul rôle, court et focalisé
# ══════════════════════════════════════════════════════════════

# Appel 1 — Sécurité uniquement
# Court → réponse rapide → si refus, STOP immédiat
_SAFETY_PROMPT = """Tu es un filtre de sécurité pour la plateforme BrandAI.

Analyse l'INTENTION RÉELLE du projet, pas les mots utilisés.

Réponds uniquement en JSON sans texte avant ou après :
{
  "safe": true ou false,
  "reason_category": null | "fraud" | "illegal" | "harmful",
  "sector": "secteur du projet (ex: tech, ecommerce, sante)",
  "confidence": 0 à 100
}

Refuse uniquement si le projet vise clairement à :
- Tromper des personnes ou leur soutirer de l'argent
- Pirater ou contourner des systèmes de sécurité
- Produire du contenu illégal dans la majorité des pays
- Inciter à la violence, la haine ou le terrorisme

RÈGLES :
- Cybersécurité ≠ hacking
- Cryptomonnaie ≠ arnaque
- Projet ambigu mais non dangereux → safe: true
- Juge l'intention, pas les mots"""


# Appel 2a — Évaluation des dimensions manquantes
# Détermine quelles questions poser à l'utilisateur
_RICHNESS_PROMPT = """Tu analyses si une description de projet contient ces 3 informations.

Réponds uniquement en JSON sans texte avant ou après :
{
  "has_problem":  true ou false,
  "has_target":   true ou false,
  "has_solution": true ou false
}

Définitions :
- has_problem  : le problème résolu est clairement mentionné
- has_target   : les utilisateurs visés sont identifiés
- has_solution : le fonctionnement de la solution est expliqué"""


# Appel 2b — Génération du JSON structuré
# Seulement si safe=true, reformule uniquement ce que l'user a dit
_CLARIFY_PROMPT = """Tu structures les idées de projets soumises par des entrepreneurs.

TON SEUL RÔLE : Reformuler ce que l'utilisateur a dit de façon claire.

NE PAS faire :
- Inventer un nom de projet     → c'est le Brand Identity Agent
- Proposer un business model    → c'est l'Idea Enhancer
- Analyser la concurrence       → c'est le Market Analysis Agent
- Inventer des informations non mentionnées par l'utilisateur

FORMAT — JSON uniquement, sans backticks :
{
  "sector":               "secteur du projet",
  "target_users":         "utilisateurs visés — uniquement ce que l'user a dit",
  "problem":              "problème résolu — uniquement ce que l'user a dit",
  "solution_description": "comment ça fonctionne — uniquement ce que l'user a dit",
  "short_pitch":          "reformulation simple en 8 à 12 mots",
  "clarity_score":        0 à 100
}

clarity_score :
- 80-100 : problème + cible + solution tous clairs
- 55-79  : 2 dimensions sur 3 présentes
- 0-54   : informations insuffisantes

Réponds toujours en français."""


# ══════════════════════════════════════════════════════════════
#  IdeaClarifierAgent
# ══════════════════════════════════════════════════════════════

class IdeaClarifierAgent(BaseAgent):
    """
    Agent 0 du pipeline BrandAI.

    2 modes d'utilisation :
      run()              → mode batch, LangGraph, sans questions
      run_interactive()  → mode chat, frontend IdeaDetail.jsx
    """

    def __init__(self):
        super().__init__(
            agent_name="idea_clarifier",
            temperature=0.2,
            max_retries=3,
        )

    # ── Méthodes abstraites requises par BaseAgent ────────────

    def _build_system_prompt(self, state: PipelineState) -> str:
        return _SAFETY_PROMPT

    def _build_user_prompt(self, state: PipelineState) -> str:
        return (
            f"Nom : {state.name}\n"
            f"Secteur : {state.sector}\n"
            f"Description : {state.description}"
        )

    # ══════════════════════════════════════════════════════════
    #  APPEL LLM 1 — check_safety()
    #  Prompt court → si refus → STOP immédiat
    # ══════════════════════════════════════════════════════════

    async def check_safety(self, state: PipelineState) -> dict:
        """
        Appel LLM 1 — sécurité uniquement.

        Retourne :
          {"safe": True}
          {"safe": False, "reason_category": str, "refusal_message": str}
        """
        user_prompt = self._build_user_prompt(state)

        try:
            raw      = await self._call_llm(_SAFETY_PROMPT, user_prompt)
            result   = self._parse_json(raw)
            safe     = bool(result.get("safe", True))
            category = result.get("reason_category") or "default"

            if not safe:
                self.logger.info(f"[idea_clarifier] Refusé — {category}")
                return {
                    "safe":            False,
                    "reason_category": category,
                    "refusal_message": get_refusal_message(category),
                }

            sector = (result.get("sector") or "").strip() or None
            confidence = result.get("confidence")
            if confidence is not None:
                try:
                    confidence = int(confidence)
                    if confidence < 0 or confidence > 100:
                        confidence = None
                except (TypeError, ValueError):
                    confidence = None
            return {"safe": True, "sector": sector, "confidence": confidence}

        except Exception as e:
            # Erreur LLM → on laisse passer par défaut
            self.logger.warning(f"[idea_clarifier] check_safety erreur : {e} → safe par défaut")
            return {"safe": True}

    # ══════════════════════════════════════════════════════════
    #  APPEL LLM 2 — generate_clarified_idea()
    #  Lancé SEULEMENT si check_safety() → safe: true
    # ══════════════════════════════════════════════════════════

    async def _evaluate_richness(self, state: PipelineState) -> dict:
        """
        Évalue quelles dimensions manquent dans la description.
        Utilisé pour décider quelles questions poser.
        """
        user_prompt = (
            f"Description : {state.description}\n"
            f"Secteur : {state.sector}\n"
            f"Public mentionné : {state.target_audience or 'non précisé'}"
        )

        try:
            raw    = await self._call_llm(_RICHNESS_PROMPT, user_prompt)
            result = self._parse_json(raw)
            return {
                "has_problem":  bool(result.get("has_problem",  False)),
                "has_target":   bool(result.get("has_target",   False)),
                "has_solution": bool(result.get("has_solution", False)),
            }
        except Exception as e:
            self.logger.warning(f"[idea_clarifier] _evaluate_richness erreur : {e}")
            return {"has_problem": False, "has_target": False, "has_solution": False}

    def build_questions(self, richness: dict) -> list[str]:
        """
        Retourne 0 à 3 questions selon les dimensions manquantes.
        Jamais de questions sur la stratégie ou la concurrence.
        """
        questions = []

        if not richness.get("has_problem"):
            questions.append(
                "Quel problème concret votre idée cherche-t-elle à résoudre ?"
            )
        if not richness.get("has_target"):
            questions.append(
                "Pour qui est cette solution ? "
                "(ex : étudiants, PME, créateurs de contenu…)"
            )
        if not richness.get("has_solution"):
            questions.append(
                "Comment votre solution fonctionne-t-elle concrètement "
                "en 2 à 3 phrases ?"
            )

        return questions

    async def generate_clarified_idea(
        self,
        state: PipelineState,
        user_answers: list[str] | None = None,
    ) -> dict:
        """
        Appel LLM 2 — clarification uniquement.
        Lancé SEULEMENT après check_safety() → safe: true.
        Reformule ce que l'utilisateur a dit. N'invente rien.
        """
        context = build_idea_summary(
            name=state.name,
            sector=state.sector,
            description=state.description,
            target_audience=state.target_audience,
        )

        answers_block = ""
        if user_answers:
            answers_block = "\n\nRéponses aux questions de clarification :"
            questions = self.build_questions(
                {"has_problem": False, "has_target": False, "has_solution": False}
            )
            for i, answer in enumerate(user_answers):
                q = questions[i] if i < len(questions) else f"Question {i+1}"
                answers_block += f"\n  Q : {q}\n  R : {answer}"

        user_prompt = f"Voici le projet soumis :\n\n{context}{answers_block}"

        try:
            raw    = await self._call_llm(_CLARIFY_PROMPT, user_prompt)
            result = self._parse_json(raw)

            return {
                "sector":               result.get("sector",               state.sector),
                "target_users":         result.get("target_users",         state.target_audience or ""),
                "problem":              result.get("problem",              ""),
                "solution_description": result.get("solution_description", state.description[:200]),
                "short_pitch":          result.get("short_pitch",          state.name),
                "clarity_score":        int(result.get("clarity_score",   50)),
            }

        except Exception as e:
            self.logger.warning(f"[idea_clarifier] generate erreur : {e} → fallback")
            return self._build_fallback(state)

    def _build_fallback(self, state: PipelineState) -> dict:
        """Fallback minimal si le LLM échoue — le pipeline ne s'arrête jamais."""
        return {
            "sector":               state.sector,
            "target_users":         state.target_audience or "",
            "problem":              "",
            "solution_description": state.description[:300],
            "short_pitch":          state.name,
            "clarity_score":        30,
        }

    # ══════════════════════════════════════════════════════════
    #  run() — mode batch (LangGraph)
    # ══════════════════════════════════════════════════════════

    async def run(self, state: PipelineState) -> dict:
        """
        Mode batch — appelé par LangGraph.

        FLUX :
          1. Validation des inputs
          2. Appel LLM 1 : check_safety()
             → safe: false → STOP, retourne le refus
          3. Appel LLM 2 : generate_clarified_idea()
             → retourne le JSON de clarification
        """
        self._log_start(state)
        state.current_agent = "idea_clarifier"

        # 1. Validation
        errors = validate_idea_input(state.name, state.description, state.sector)
        if errors:
            msg = "; ".join(errors)
            state.errors.append(f"idea_clarifier: {msg}")
            raise ValueError(f"Validation échouée : {msg}")

        # 2. Appel LLM 1 — sécurité
        safety = await self.check_safety(state)

        if not safety["safe"]:
            state.status = "refused"
            state.errors.append(
                f"idea_clarifier: refusé — {safety.get('reason_category')}"
            )
            return {
                "safe":            False,
                "reason_category": safety.get("reason_category"),
                "refusal_message": safety.get("refusal_message"),
                "clarified_idea":  {},
                "clarity_score":   0,
            }

        # 3. Appel LLM 2 — clarification
        clarified = await self.generate_clarified_idea(state)
        score     = clarified.get("clarity_score", 50)

        state.clarified_idea = clarified
        state.clarity_score  = score

        self._log_success(clarified)
        return {
            "safe":           True,
            "clarified_idea": clarified,
            "clarity_score":  score,
        }

    # ══════════════════════════════════════════════════════════
    #  run_interactive() — mode chat (frontend IdeaDetail.jsx)
    # ══════════════════════════════════════════════════════════

    async def run_interactive(
        self,
        state: PipelineState,
        user_answers: list[str] | None = None,
    ) -> dict:
        """
        Mode chat — appelé depuis IdeaDetail.jsx.

        Frontend appel A — sans réponses :
          1. Validation inputs
          2. LLM 1 : check_safety()  → si refus → STOP
          3. LLM 2 : _evaluate_richness() → dimensions manquantes
          4. Retourne les questions
          → {"questions": [...], "ready": false}

        Frontend appel B — avec réponses :
          1. LLM 2 : generate_clarified_idea() avec les réponses
          → {"clarified_idea": {...}, "ready": true}
        """
        self._log_start(state)

        # Validation
        errors = validate_idea_input(state.name, state.description, state.sector)
        if errors:
            return {
                "safe":           True,
                "questions":      [],
                "clarified_idea": {},
                "clarity_score":  0,
                "ready":          False,
                "error":          "; ".join(errors),
            }

        # ── Appel B : l'utilisateur a répondu aux questions ──────────────
        if user_answers:
            clarified = await self.generate_clarified_idea(state, user_answers)
            score     = clarified.get("clarity_score", 50)

            state.clarified_idea = clarified
            state.clarity_score  = score

            self._log_success(clarified)
            return {
                "safe":           True,
                "questions":      [],
                "clarified_idea": clarified,
                "clarity_score":  score,
                "ready":          True,
            }

        # ── Appel A : premier appel, sans réponses ────────────────────────

        # LLM 1 — sécurité
        safety = await self.check_safety(state)

        if not safety["safe"]:
            state.status = "refused"
            return {
                "safe":            False,
                "reason_category": safety.get("reason_category"),
                "refusal_message": safety.get("refusal_message"),
                "questions":       [],
                "clarified_idea":  {},
                "clarity_score":   0,
                "ready":           False,
            }

        # LLM 2a — dimensions manquantes
        richness  = await self._evaluate_richness(state)
        questions = self.build_questions(richness)

        if questions:
            return {
                "safe":           True,
                "questions":      questions,
                "clarified_idea": {},
                "clarity_score":  0,
                "ready":          False,
            }

        # Description complète → générer directement sans questions
        # LLM 2b — clarification directe
        clarified = await self.generate_clarified_idea(state)
        score     = clarified.get("clarity_score", 50)

        state.clarified_idea = clarified
        state.clarity_score  = score

        self._log_success(clarified)
        return {
            "safe":           True,
            "questions":      [],
            "clarified_idea": clarified,
            "clarity_score":  score,
            "ready":          True,
        }