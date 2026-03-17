# ══════════════════════════════════════════════════════════════
#  backend-ai/agents/idea_clarifier.py
#  Agent 0 — Idea Clarifier
#
#  RÔLE UNIQUE : Comprendre ce que l'utilisateur veut faire.
#
#  FLUX — 2 appels LLM séquentiels :
#    Appel 1 : check_safety()     → sécurité + détection secteur
#    Appel 2 : generate_clarified_idea() → 3 types de réponse :
#      - "questions"  : dimensions manquantes → poser des questions
#      - "off_topic"  : réponse hors sujet → rediriger poliment
#      - "clarified"  : idée complète → JSON structuré + score
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
from tools.idea_tools import build_idea_summary


# ══════════════════════════════════════════════════════════════
#  PROMPTS
# ══════════════════════════════════════════════════════════════

_SAFETY_PROMPT = """Tu es un filtre de sécurité pour la plateforme BrandAI.

Analyse l'INTENTION RÉELLE du projet, pas les mots utilisés.
Déduis aussi le SECTEUR depuis la description.

Réponds uniquement en JSON sans texte avant ou après :
{
  "safe": true ou false,
  "reason_category": null | "fraud" | "illegal" | "harmful",
  "sector": "secteur principal (tech, ecommerce, sante, education, finance, autre)",
  "confidence": 0 à 100
}

Refuse uniquement si le projet vise clairement à :
- Tromper des personnes ou soutirer de l'argent
- Pirater des systèmes de sécurité
- Produire du contenu illégal
- Inciter à la violence ou au terrorisme

RÈGLES :
- Cybersécurité ≠ hacking
- Cryptomonnaie ≠ arnaque
- Projet ambigu → safe: true
- Juge l'intention, pas les mots"""


_RICHNESS_PROMPT = """Tu analyses si une description contient ces 3 informations.

Réponds uniquement en JSON sans texte avant ou après :
{
  "has_problem":  true ou false,
  "has_target":   true ou false,
  "has_solution": true ou false
}

Définitions :
- has_problem  : le problème résolu est mentionné
- has_target   : les utilisateurs visés sont identifiés
- has_solution : le fonctionnement est expliqué"""


_CLARIFY_PROMPT = """Tu es l'agent Clarifier de BrandAI.
Tu aides les entrepreneurs à structurer leur idée.

TON RÔLE : Comprendre et reformuler ce que l'utilisateur a dit.
Ne rien inventer. Ne jamais copier du texte depuis ces instructions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RÈGLES ABSOLUES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Ne jamais inventer d'informations
- Ne jamais proposer de business model → Idea Enhancer
- Ne jamais générer un nom → Brand Identity
- Ne jamais analyser la concurrence → Market Analysis
- Toujours répondre en français
- Toujours répondre en JSON pur sans backticks
- Le champ "message" : toujours rédigé librement par toi
  jamais copié depuis ces instructions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DÉTECTION HORS SUJET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Réponse hors sujet si elle ne répond pas à la question :
- Salutations : "bonjour", "ok", "merci"
- Questions techniques : "c'est quoi React ?"
- Moins de 4 mots sans information utile

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMAT — 3 types de réponse possibles
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TYPE 1 — "questions" (score < 80, dimensions manquantes) :
{
  "type": "questions",
  "message": <
    Rédige librement 1-2 phrases encourageantes en français.
    Mentionne le secteur ou le type de projet si connu.
    Introduis naturellement les questions qui suivent.
    Varie le style à chaque fois.
    Ne jamais copier ce texte depuis ces instructions.
  >,
  "questions": ["question 1", "question 2"],
  "score": <entier entre 0 et 79>
}

TYPE 2 — "off_topic" (réponse hors sujet) :
{
  "type": "off_topic",
  "message": <
    Rédige librement 2-3 phrases polies en français.
    Explique que tu es un agent de clarification d'idée.
    Précise que ton rôle est de préparer l'idée pour
    le pipeline de génération de marque.
    Invite à revenir à la question.
    Varie le style à chaque fois.
    Ne jamais copier ce texte depuis ces instructions.
  >,
  "repeat_question": <question précédente mot pour mot>
}

TYPE 3 — "clarified" (score >= 80, toutes dimensions) :
{
  "type": "clarified",
  "message": <
    Rédige librement 1-2 phrases en français.
    Score >= 90 : ton enthousiaste, félicite l'entrepreneur.
    Score 80-89 : ton positif et encourageant.
    Mentionne concrètement l'idée ou le secteur.
    Annonce que la structure est prête pour le pipeline.
    Varie le style selon le projet.
    Ne jamais copier ce texte depuis ces instructions.
  >,
  "sector":               <secteur détecté ou déduit>,
  "target_users":         <uniquement ce que l'user a dit>,
  "problem":              <uniquement ce que l'user a dit>,
  "solution_description": <uniquement ce que l'user a dit>,
  "short_pitch":          <reformulation 8-12 mots>,
  "score": <entier entre 80 et 100>
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCORE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- problème mentionné  : +33 pts
- cible identifiée    : +33 pts
- solution expliquée  : +34 pts

80-100 → type "clarified"
55-79  → type "questions"
0-54   → type "questions"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HISTORIQUE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Si un historique est fourni, prends en compte TOUTES
les réponses précédentes pour réévaluer le score.
Ne repose jamais une question déjà bien répondue.
"""


# ══════════════════════════════════════════════════════════════
#  IdeaClarifierAgent
# ══════════════════════════════════════════════════════════════

class IdeaClarifierAgent(BaseAgent):
    """
    Agent 0 du pipeline BrandAI.

    2 modes :
      run()              → mode batch (LangGraph)
      run_interactive()  → mode chat (frontend IdeaPage.jsx)
    """

    def __init__(self):
        super().__init__(
            agent_name="idea_clarifier",
            temperature=0.3,
            max_retries=3,
        )

    def _build_system_prompt(self, state: PipelineState) -> str:
        return _SAFETY_PROMPT

    def _build_user_prompt(self, state: PipelineState) -> str:
        parts = []
        if state.name and state.name.strip():
            parts.append(f"Nom : {state.name}")
        if state.sector and state.sector.strip():
            parts.append(f"Secteur : {state.sector}")
        parts.append(f"Description : {state.description}")
        return "\n".join(parts)

    # ══════════════════════════════════════════════════════════
    #  LLM 1 — check_safety()
    # ══════════════════════════════════════════════════════════

    async def check_safety(self, state: PipelineState) -> dict:
        user_prompt = self._build_user_prompt(state)
        try:
            raw    = await self._call_llm(_SAFETY_PROMPT, user_prompt)
            self.logger.info(f"[safety] raw : {repr(raw[:300])}")
            result = self._parse_json(raw)
            safe   = bool(result.get("safe", True))

            if not safe:
                category = result.get("reason_category") or "default"
                self.logger.info(f"[clarifier] Refusé — {category}")
                return {
                    "safe":            False,
                    "reason_category": category,
                    "refusal_message": get_refusal_message(category),
                }

            sector     = (result.get("sector") or "").strip() or None
            confidence = result.get("confidence")
            if confidence is not None:
                try:
                    confidence = int(confidence)
                    if not (0 <= confidence <= 100):
                        confidence = None
                except (TypeError, ValueError):
                    confidence = None

            return {"safe": True, "sector": sector, "confidence": confidence}

        except Exception as e:
            self.logger.warning(f"[clarifier] check_safety erreur : {e}")
            return {"safe": True}

    # ══════════════════════════════════════════════════════════
    #  LLM 2a — _evaluate_richness()
    # ══════════════════════════════════════════════════════════

    async def _evaluate_richness(self, state: PipelineState) -> dict:
        user_prompt = (
            f"Description : {state.description}\n"
            f"Secteur : {state.sector or 'à détecter'}\n"
            f"Public : {state.target_audience or 'non précisé'}"
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
            self.logger.warning(f"[clarifier] _evaluate_richness erreur : {e}")
            return {
                "has_problem":  False,
                "has_target":   False,
                "has_solution": False,
            }

    def build_questions(self, richness: dict) -> list[str]:
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
                "Comment votre solution fonctionne-t-elle "
                "concrètement en 2 à 3 phrases ?"
            )
        return questions

    # ══════════════════════════════════════════════════════════
    #  LLM 2b — generate_clarified_idea()
    #  Retourne : "questions" | "off_topic" | "clarified"
    # ══════════════════════════════════════════════════════════

    async def generate_clarified_idea(
        self,
        state: PipelineState,
        user_answers: list[str] | None = None,
        conversation_history: list[dict] | None = None,
    ) -> dict:
        """
        Appel LLM principal.
        Retourne un dict avec "type" = questions | off_topic | clarified.
        Le champ "message" est rédigé librement par le LLM.
        """
        context = build_idea_summary(
            name=state.name,
            sector=state.sector,
            description=state.description,
            target_audience=state.target_audience,
        )

        # Historique complet
        history_block = ""
        if conversation_history:
            history_block = "\n\nHistorique de la conversation :"
            for turn in conversation_history:
                q = turn.get("question", "")
                a = turn.get("answer", "")
                if q or a:
                    history_block += f"\n  Agent : {q}\n  User  : {a}"

        # Dernières réponses
        answers_block = ""
        if user_answers:
            answers_block = "\n\nDernières réponses reçues :"
            for i, answer in enumerate(user_answers):
                answers_block += f"\n  Réponse {i+1} : {answer}"

        user_prompt = (
            f"Projet :\n\n{context}"
            f"{history_block}"
            f"{answers_block}"
        )

        try:
            raw = await self._call_llm(_CLARIFY_PROMPT, user_prompt)
            self.logger.info(f"[clarifier] raw : {repr(raw[:500])}")

            result      = self._parse_json(raw)
            result_type = result.get("type", "clarified")

            self.logger.info(f"[clarifier] type : {result_type}")
            self.logger.info(
                f"[clarifier] message : {result.get('message', '')[:100]}"
            )

            # ── off_topic ───────────────────────────────────
            if result_type == "off_topic":
                return {
                    "type":            "off_topic",
                    "message":         result.get("message", ""),
                    "repeat_question": result.get("repeat_question", ""),
                }

            # ── questions ───────────────────────────────────
            if result_type == "questions":
                return {
                    "type":      "questions",
                    "message":   result.get("message", ""),
                    "questions": result.get("questions", []),
                    "score":     int(result.get("score", 45)),
                }

            # ── clarified ───────────────────────────────────
            return {
                "type":               "clarified",
                "message":            result.get("message", ""),
                "sector":             result.get("sector", state.sector or ""),
                "target_users":       result.get("target_users", ""),
                "problem":            result.get("problem", ""),
                "solution_description": result.get("solution_description", ""),
                "short_pitch":        result.get("short_pitch", ""),
                "score":              int(result.get("score", 50)),
            }

        except Exception as e:
            self.logger.warning(f"[clarifier] generate erreur : {e} → fallback")
            return self._build_fallback(state)

    def _build_fallback(self, state: PipelineState) -> dict:
        return {
            "type":               "clarified",
            "message":            "Voici ce que j'ai compris de votre projet :",
            "sector":             state.sector or "",
            "target_users":       state.target_audience or "",
            "problem":            "",
            "solution_description": state.description[:300],
            "short_pitch":        state.name or "",
            "score":              30,
        }

    # ══════════════════════════════════════════════════════════
    #  run() — mode batch (LangGraph)
    # ══════════════════════════════════════════════════════════

    async def run(self, state: PipelineState) -> dict:
        self._log_start(state)
        state.current_agent = "idea_clarifier"

        if not state.description or len(state.description.strip()) < 10:
            raise ValueError("Description trop courte")

        # LLM 1 — sécurité
        safety = await self.check_safety(state)
        if safety.get("sector") and not state.sector:
            state.sector = safety["sector"]

        if not safety["safe"]:
            state.status = "refused"
            return {
                "safe":            False,
                "reason_category": safety.get("reason_category"),
                "refusal_message": safety.get("refusal_message"),
                "clarified_idea":  {},
                "clarity_score":   0,
            }

        # LLM 2 — clarification
        result = await self.generate_clarified_idea(state)
        score  = result.get("score", 50)

        clarified = {
            k: v for k, v in result.items()
            if k not in ("type", "message")
        }
        clarified["clarity_score"] = score

        state.clarified_idea = clarified
        state.clarity_score  = score
        self._log_success(clarified)

        return {
            "safe":           True,
            "clarified_idea": clarified,
            "clarity_score":  score,
        }

    # ══════════════════════════════════════════════════════════
    #  run_interactive() — mode chat (frontend IdeaPage.jsx)
    # ══════════════════════════════════════════════════════════

    async def run_interactive(
        self,
        state: PipelineState,
        user_answers: list[str] | None = None,
        conversation_history: list[dict] | None = None,
    ) -> dict:
        """
        Mode chat — appelé depuis clarifier.py (routes SSE).

        Appel A (sans réponses) :
          1. check_safety() → secteur détecté
          2. generate_clarified_idea() → questions ou clarified

        Appel B (avec réponses) :
          1. generate_clarified_idea() avec historique complet
          → off_topic | questions | clarified
        """
        self._log_start(state)

        if not state.description or len(state.description.strip()) < 5:
            return {
                "type":      "questions",
                "message":   "Pourriez-vous décrire votre idée en quelques mots ?",
                "questions": ["Décrivez votre idée en quelques phrases."],
                "score":     0,
            }

        # ── Appel B — avec réponses ───────────────────────────
        if user_answers:
            result = await self.generate_clarified_idea(
                state,
                user_answers=user_answers,
                conversation_history=conversation_history or [],
            )

            if result.get("type") == "clarified":
                score     = result.get("score", 50)
                clarified = {
                    k: v for k, v in result.items()
                    if k not in ("type", "message")
                }
                clarified["clarity_score"] = score
                state.clarified_idea = clarified
                state.clarity_score  = score
                self._log_success(clarified)

            return result

        # ── Appel A — premier appel ───────────────────────────

        # LLM 1 — sécurité + détection secteur
        safety = await self.check_safety(state)
        if safety.get("sector") and not state.sector:
            state.sector = safety["sector"]

        if not safety["safe"]:
            state.status = "refused"
            return {
                "type":            "refused",
                "safe":            False,
                "reason_category": safety.get("reason_category"),
                "refusal_message": safety.get("refusal_message"),
                "message":         safety.get("refusal_message", ""),
                "score":           0,
            }

        # LLM 2 — clarification ou questions
        result = await self.generate_clarified_idea(state)

        if result.get("type") == "clarified":
            score     = result.get("score", 50)
            clarified = {
                k: v for k, v in result.items()
                if k not in ("type", "message")
            }
            clarified["clarity_score"] = score
            state.clarified_idea = clarified
            state.clarity_score  = score
            self._log_success(clarified)

        return result