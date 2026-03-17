from agents.base_agent import BaseAgent, PipelineState
from guardrails.safety_checks import get_refusal_message
from tools.idea_tools import build_idea_summary


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


_QUESTIONS_PROMPT = """Tu es l'agent Clarifier de BrandAI.
Tu analyses une idée de projet et génères exactement
3 questions pour mieux la comprendre.

RÈGLES :
- Toujours répondre en français
- Toujours répondre en JSON pur sans backticks
- Le champ "message" : rédigé librement, adapté à l'idée
- Ne jamais répéter un mot deux fois de suite
- Phrases courtes et directes

QUESTIONS AUTORISÉES — exactement ces 3 :
1. Quel problème concret résolvez-vous ?
2. Pour qui est cette solution ?
3. Comment fonctionne-t-elle concrètement ?

Adapter la formulation selon le secteur détecté.
Ne jamais poser de questions sur la concurrence,
le business model ou la stratégie.

FORMAT JSON :
{
  "type": "questions",
  "message":
    1-2 phrases d'accueil bienveillantes en français.
    Mentionne le secteur ou type de projet si connu.
    Annonce que tu as besoin de 3 précisions.
    Ton encourageant. Varie le style.
    Ne jamais copier depuis ces instructions.
  >,
  "questions": [
    <question sur le problème — adaptée au secteur>,
    <question sur la cible — adaptée au secteur>,
    <question sur la solution — adaptée au secteur>
  ]
}
"""


_CLARIFY_PROMPT = """Tu es l'agent Clarifier de BrandAI.
Tu structures une idée de projet avec toutes les informations
fournies par l'entrepreneur.

TON RÔLE : Reformuler ce que l'utilisateur a dit.
Ne rien inventer. Ne rien ajouter.

RÈGLES :
- Toujours répondre en français
- Toujours répondre en JSON pur sans backticks
- Ne jamais inventer d'informations
- Ne jamais proposer business model → Idea Enhancer
- Ne jamais générer un nom → Brand Identity
- Ne jamais répéter un mot deux fois de suite

FORMAT JSON :
{
  "type": "clarified",
  "message":
    1-2 phrases de confirmation en français.
    Score >= 90 : ton enthousiaste.
    Score 80-89 : ton encourageant.
    Score < 80 : ton neutre mais positif.
    Mentionne concrètement l'idée ou le secteur.
    Varie le style. Ne jamais copier ces instructions.
  >,
  "sector":               <secteur détecté>,
  "target_users":         <ce que l'user a dit>,
  "problem":              <ce que l'user a dit>,
  "solution_description": <ce que l'user a dit>,
  "short_pitch":          <reformulation 8-12 mots>,
  "score":
    Évalue honnêtement :
    - problème clairement mentionné  : +33 pts
    - cible identifiée               : +33 pts
    - solution expliquée             : +34 pts
    Total sur 100.
  >
}
"""


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

    async def check_safety(self, state: PipelineState) -> dict:
        user_prompt = self._build_user_prompt(state)
        try:
            raw = await self._call_llm(_SAFETY_PROMPT, user_prompt)
            self.logger.info(f"[safety] raw : {repr(raw[:300])}")
            result = self._parse_json(raw)
            safe = bool(result.get("safe", True))

            if not safe:
                category = result.get("reason_category") or "default"
                self.logger.info(f"[clarifier] Refusé — {category}")
                return {
                    "safe": False,
                    "reason_category": category,
                    "refusal_message": get_refusal_message(category),
                }

            sector = (result.get("sector") or "").strip() or None
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

    async def generate_questions(self, state: PipelineState) -> dict:
        """
        Appel LLM 1 — génère les 3 questions.
        Appelé au premier appel depuis le frontend.
        """
        user_prompt = self._build_user_prompt(state)

        try:
            raw = await self._call_llm(_QUESTIONS_PROMPT, user_prompt)
            self.logger.info(f"[clarifier] questions raw : {repr(raw[:300])}")
            result = self._parse_json(raw)

            return {
                "type": "questions",
                "message": result.get("message", ""),
                "questions": result.get(
                    "questions",
                    [
                        "Quel problème concret votre idée résout-elle ?",
                        "Pour qui est cette solution ?",
                        "Comment fonctionne-t-elle concrètement ?",
                    ],
                ),
            }
        except Exception as e:
            self.logger.warning(f"[clarifier] generate_questions erreur : {e}")
            return {
                "type": "questions",
                "message": "Pour mieux comprendre votre idée, j'ai besoin de 3 précisions :",
                "questions": [
                    "Quel problème concret votre idée résout-elle ?",
                    "Pour qui est cette solution ?",
                    "Comment fonctionne-t-elle concrètement ?",
                ],
            }

    async def generate_clarified_idea(
        self,
        state: PipelineState,
        answers: dict | None = None,
    ) -> dict:
        """
        Appel LLM 2 — génère le JSON final.
        answers = {"problem": "...", "target": "...", "solution": "..."}
        """
        context = build_idea_summary(
            name=state.name,
            sector=state.sector,
            description=state.description,
            target_audience=state.target_audience,
        )

        answers_block = ""
        if answers:
            answers_block = "\n\nRéponses de l'entrepreneur :"
            if answers.get("problem"):
                answers_block += f"\n  Problème  : {answers['problem']}"
            if answers.get("target"):
                answers_block += f"\n  Cible     : {answers['target']}"
            if answers.get("solution"):
                answers_block += f"\n  Solution  : {answers['solution']}"

        user_prompt = f"Projet :\n\n{context}{answers_block}"

        try:
            raw = await self._call_llm(_CLARIFY_PROMPT, user_prompt)
            self.logger.info(f"[clarifier] clarify raw : {repr(raw[:500])}")
            result = self._parse_json(raw)

            return {
                "type": "clarified",
                "message": result.get("message", ""),
                "sector": result.get("sector", state.sector or ""),
                "target_users": result.get("target_users", ""),
                "problem": result.get("problem", ""),
                "solution_description": result.get(
                    "solution_description", ""
                ),
                "short_pitch": result.get("short_pitch", ""),
                "score": int(result.get("score", 50)),
            }
        except Exception as e:
            self.logger.warning(f"[clarifier] generate erreur : {e}")
            return self._build_fallback(state, answers)

    def _build_fallback(
        self,
        state: PipelineState,
        answers: dict | None = None,
    ) -> dict:
        return {
            "type": "clarified",
            "message": "Voici ce que j'ai compris de votre projet :",
            "sector": state.sector or "",
            "target_users": (answers or {}).get("target", ""),
            "problem": (answers or {}).get("problem", ""),
            "solution_description": (answers or {}).get(
                "solution", state.description[:300]
            ),
            "short_pitch": state.name or "",
            "score": 40,
        }

    async def run(self, state: PipelineState) -> dict:
        """
        Mode batch : check_safety puis clarification directe
        (sans questions intermédiaires).
        """
        self._log_start(state)
        state.current_agent = "idea_clarifier"

        if not state.description or len(state.description.strip()) < 10:
            raise ValueError("Description trop courte")

        safety = await self.check_safety(state)
        if safety.get("sector") and not state.sector:
            state.sector = safety["sector"]

        if not safety["safe"]:
            state.status = "refused"
            return {
                "safe": False,
                "reason_category": safety.get("reason_category"),
                "refusal_message": safety.get("refusal_message"),
                "clarified_idea": {},
                "clarity_score": 0,
            }

        result = await self.generate_clarified_idea(state, answers=None)
        score = result.get("score", 50)

        clarified = {k: v for k, v in result.items() if k not in ("type", "message")}
        clarified["clarity_score"] = score

        state.clarified_idea = clarified
        state.clarity_score = score
        self._log_success(clarified)

        return {
            "safe": True,
            "clarified_idea": clarified,
            "clarity_score": score,
        }

    async def run_interactive(
        self,
        state: PipelineState,
        answers: dict | None = None,
    ) -> dict:
        """
        Appel A (answers=None) → check_safety + generate_questions
        Appel B (answers={...}) → generate_clarified_idea
        """
        self._log_start(state)

        if not state.description or len(state.description.strip()) < 5:
            return {
                "type": "questions",
                "message": "Décrivez votre idée pour commencer.",
                "questions": [
                    "Quel problème concret votre idée résout-elle ?",
                    "Pour qui est cette solution ?",
                    "Comment fonctionne-t-elle concrètement ?",
                ],
            }

        # Appel B — avec réponses
        if answers:
            result = await self.generate_clarified_idea(state, answers)
            if result.get("score", 0) >= 55:
                score = result.get("score", 50)
                clarified = {
                    k: v for k, v in result.items() if k not in ("type", "message")
                }
                clarified["clarity_score"] = score
                state.clarified_idea = clarified
                state.clarity_score = score
                self._log_success(clarified)
            return result

        # Appel A — premier appel
        safety = await self.check_safety(state)
        if safety.get("sector") and not state.sector:
            state.sector = safety["sector"]

        if not safety["safe"]:
            state.status = "refused"
            return {
                "type": "refused",
                "message": safety.get("refusal_message", ""),
                "reason_category": safety.get("reason_category"),
                "score": 0,
            }

        result = await self.generate_questions(state)
        return result