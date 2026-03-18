# backend-ai/agents/idea_clarifier.py
import re
import logging

from agents.base_agent import BaseAgent, PipelineState
from guardrails.safety_checks import get_refusal_message
from tools.idea_tools import build_idea_summary, validate_idea_input

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# UTILITAIRE — Détection texte incohérent SANS LLM
# ══════════════════════════════════════════════════════════════════════
def is_gibberish(text: str) -> bool:
    """
    Filtre basique SANS LLM — détecte les cas évidents :
    - Texte trop court (< 10 chars)
    - Moins de 2 mots
    - Mots sans aucune voyelle (ex: "qsdfsdfg")
    - Tous les mots identiques
    Le LLM gère les cas ambigus.
    """
    if not text or len(text.strip()) < 10:
        return True

    vowels = set("aeiouyàâéèêëîïôùûüœ")
    words = re.findall(r"\w+", text.lower())

    if len(words) < 2:
        return True

    if len(set(words)) == 1:
        return True

    real_words = sum(1 for w in words if len(w) <= 2 or any(c in vowels for c in w))
    if real_words < 2:
        return True

    for word in words:
        if len(word) > 6:
            ratio = sum(1 for c in word if c in vowels) / len(word)
            if ratio < 0.15:
                return True

    return False


# ══════════════════════════════════════════════════════════════
# PROMPTS (inchangés)
# ══════════════════════════════════════════════════════════════
_SAFETY_PROMPT = """Tu es un système de modération pour BrandAI.

Ta mission : analyser l'INTENTION RÉELLE du projet.

RÈGLE CRITIQUE :
Quand des réponses utilisateur sont fournies,
analyse l'ENSEMBLE description + réponses.
Une description innocente avec des réponses malveillantes
= projet REFUSÉ immédiatement.

Exemples concrets :
- Description "marketplace" + réponse "vente de drogue"
  → safe: false, reason_category: "illegal"
- Description "app mobile" + réponse "escroquer des retraités"
  → safe: false, reason_category: "fraud"
- Description "marketplace" + réponse "vêtements pour enfants"
  → safe: true

Réponds STRICTEMENT en JSON valide, sans texte avant ou après :

{
  "safe": true ou false,
  "reason_category": null | "fraud" | "illegal" | "harmful",
  "sector": "tech | ecommerce | sante | education | finance | autre",
  "confidence": nombre entre 0 et 100
}

Refuser si l'intention est clairement :
- Tromper / escroquer des personnes (fraud)
- Activités illégales : drogues, armes, contrebande,
  faux documents, piratage (illegal)
- Contenu nuisible, violent, dangereux (harmful)
- Exploitation de mineurs (harmful)

RÈGLES :
- Cybersécurité défensive ≠ hacking malveillant
- Crypto légal ≠ arnaque
- Projet flou sans intention claire → safe: true
- Juger l'INTENTION RÉELLE, pas les mots isolés
- Si les réponses révèlent une intention illégale → safe: false
- En cas de doute → safe: true"""

_REFUSAL_PROMPT = """Tu es l'agent Clarifier de BrandAI.

Un projet vient d'être refusé par notre système de modération.
Tu dois expliquer à l'entrepreneur pourquoi BrandAI
ne peut pas l'accompagner.

RÈGLES :
- Répondre en français
- Ton professionnel, jamais agressif
- Mentionner que c'est basé sur la description
  et les réponses fournies
- Expliquer clairement la raison du refus
- Ne pas insulter l'utilisateur
- Proposer de soumettre un nouveau projet
- Maximum 3 phrases

CATÉGORIES :
fraud   → Le projet vise à tromper ou escroquer des personnes.
illegal → Le projet implique des activités contraires à la loi.
harmful → Le projet pourrait causer du tort à des personnes.

STRUCTURE :
Phrase 1 : "En nous basant sur votre description et
            vos réponses, [raison du refus]."
Phrase 2 : Pourquoi BrandAI ne peut pas accompagner.
Phrase 3 : Invitation à soumettre un nouveau projet légal.

Réponds UNIQUEMENT avec le message en texte libre.
Pas de JSON, pas de titre, juste le message."""

QUESTIONS_PROMPT = """Tu es l'agent Idea Clarifier de BrandAI.

Ton rôle est d'aider un entrepreneur à clarifier son idée
en analysant sa description et en vérifiant si elle est complète.

Une idée est considérée comme claire si ces 3 éléments sont définis :
1. PROBLÈME — quel problème concret est résolu ?
2. CIBLE — qui sont les utilisateurs ?
3. SOLUTION — comment fonctionne la solution ?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RÈGLES STRICTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Répondre uniquement en français
- Répondre uniquement en JSON valide (aucun markdown, aucun backticks)
- Ne jamais répéter un mot deux fois de suite
- Ne jamais inventer des informations absentes
- Adapter au secteur détecté automatiquement
- Maximum 3 questions
- Poser uniquement les questions nécessaires (pas systématiquement 3)
- Pour le JSON :
  - Si type="questions" alors renvoyer `missing_axes` ET `questions`
  - Chaque élément de `questions` doit être un objet {axis,text}
  - questions.length doit être égal à missing_axes.length
  - axis doit être exactement "problem" | "target" | "solution"
  - missing_axes ne doit contenir que les axes absents ou ambigus dans la DESCRIPTION
  - Ne pas inclure un axe dans missing_axes s'il est clairement exprimé

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANALYSE DE L’IDÉE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Lire la description utilisateur
2. Détecter si les éléments suivants sont présents et clairs :
- problème
- cible
- solution

3. Considérer comme "non clair" si :
- trop vague
- trop général
- implicite
- ambigu
- ou absent

4. Si le texte est incohérent ou aléatoire (ex: "qsdjkfqsdf"),
→ considérer comme non exploitable

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LOGIQUE DE DÉCISION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CAS A — IDÉE CLAIRE :
→ Les 3 éléments sont présents et compréhensibles
→ Ne poser AUCUNE question
→ Reformuler clairement l’idée

CAS B — IDÉE PARTIELLE :
→ Certains éléments manquent ou sont flous
→ Poser UNIQUEMENT les questions nécessaires
→ Chaque question doit cibler un élément manquant

CAS C — IDÉE TROP VAGUE OU INCOHÉRENTE :
→ Expliquer que la description n’est pas claire
→ Poser des questions simples pour structurer

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTERDIT DANS LES QUESTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- concurrence
- différenciation
- business model
- pricing
- stratégie marketing

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STYLE DES QUESTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Courtes et précises
- Adaptées au contexte
- Naturelles (pas robotiques)
- Une question = un objectif

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMAT DE SORTIE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CAS A — IDÉE CLAIRE :
{
  "type": "clarified",
  "message": "Votre idée est claire et bien structurée.",
  "missing_axes": [],
  "questions": []
}

CAS B — QUESTIONS :
{
  "type": "questions",
  "message": "Votre idée est intéressante, mais certains éléments doivent être précisés.",
  "missing_axes": ["problem"],
  "questions": [
    {"axis": "problem", "text": "Quel problème concret voulez-vous résoudre ?"}
  ]
}

CAS C — IDÉE NON CLAIRE :
{
  "type": "questions",
  "message": "Votre description est trop vague ou difficile à comprendre. Quelques précisions vont m’aider à mieux structurer votre idée.",
  "missing_axes": ["problem", "target", "solution"],
  "questions": [
    {"axis": "problem",  "text": "Quel problème voulez-vous résoudre ?"},
    {"axis": "target",   "text": "Pour qui est cette solution ?"},
    {"axis": "solution", "text": "Quelle solution proposez-vous ?"}
  ]
}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OBJECTIF FINAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Toujours produire soit :
- une idée claire, exploitable directement par les autres agents
- soit les questions minimales nécessaires pour y arriver
Ne jamais faire de résumé inutile.
Ne jamais ajouter d’explications hors JSON.
"""

_CLARIFY_PROMPT = """Tu es l'agent Idea Clarifier de BrandAI.

Ton rôle est de transformer une idée utilisateur en description
claire et structurée, SANS ajouter de nouvelles idées.

OBJECTIF :
- Problème : précis, concret, compréhensible
- Cible : bien définie (qui exactement ?)
- Solution : concrète, simple, claire

RÈGLES STRICTES :
- Répondre en français
- Répondre en JSON valide (sans backticks ni markdown)
- Ne jamais inventer d'informations
- Ne jamais proposer de stratégie ou business model
- Reformuler pour améliorer la clarté, rester fidèle

GARDE-FOU SÉCURITÉ :
Si description ou réponses contiennent des activités
illégales ou nuisibles :
→ Ne JAMAIS reformuler ces activités comme légales
→ Ne JAMAIS présenter une intention illégale positivement
→ Retourner score: 0 dans ce cas

SCORING :
- problème clair    : +33 pts
- cible claire      : +33 pts
- solution claire   : +34 pts
- Score 80-100 → idée prête pour le pipeline

TON selon score :
- score ≥ 90 → enthousiaste
- score 80-89 → encourageant
- score < 80 → neutre positif, encourager à préciser

FORMAT JSON :
{
  "type": "clarified",
  "message": "1-2 phrases naturelles confirmant la compréhension",
  "sector": "secteur détecté",
  "target_users": "cible  définie",
  "problem": "problème clair et reformulé",
  "solution_description": "solution expliquée concrètement",
  "short_pitch": "phrase de 8 à 12 mots maximum",
  "score": nombre entre 0 et 100
}"""


# ══════════════════════════════════════════════════════════════
# AGENT
# ══════════════════════════════════════════════════════════════
class IdeaClarifierAgent(BaseAgent):
    """
    Agent 0 du pipeline BrandAI.
    Valide, questionne et structure l'idée utilisateur.

    Sécurité :
    - check_safety sans answers sur l'appel 1
    - check_safety avec answers sur l'appel 2
    """

    def __init__(self):
        super().__init__(agent_name="idea_clarifier", temperature=0.3, max_retries=3)
        # Groq uniquement — température 0.05 forcée (voir LLMRotator)
        self.llm_rotator = self.llm_rotator.groq_only()

    def _build_system_prompt(self, state: PipelineState) -> str:
        return _CLARIFY_PROMPT

    def _build_user_prompt(self, state: PipelineState, answers: dict | None = None) -> str:
        """
        Construit le prompt envoyé au LLM.
        Si answers présent → séparateurs ━━━ pour rendre les réponses visibles au LLM.
        """
        parts = []

        if state.name and state.name.strip():
            parts.append(f"Nom du projet : {state.name}")

        if state.sector and state.sector.strip():
            parts.append(f"Secteur : {state.sector}")

        parts.append(f"Description : {state.description}")

        if state.target_audience and state.target_audience.strip():
            parts.append(f"Public cible mentionné : {state.target_audience}")

        if answers:
            parts.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            parts.append("RÉPONSES DE L'UTILISATEUR — analyser attentivement l'intention :")
            parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            if answers.get("problem"):
                parts.append(f"Problème déclaré   : {answers['problem']}")
            if answers.get("target"):
                parts.append(f"Cible déclarée     : {answers['target']}")
            if answers.get("solution"):
                parts.append(f"Solution déclarée  : {answers['solution']}")

            parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            parts.append(
                "Question : ces réponses révèlent-elles une intention illégale ou nuisible ?"
            )

        return "\n".join(parts)

    async def check_safety(self, state: PipelineState, answers: dict | None = None) -> dict:
        """
        Vérifie la conformité du projet via LLM.
        Appel 1 (answers=None) : analyse description seule
        Appel 2 (answers=...) : analyse description + réponses ensemble
        """
        user_prompt = self._build_user_prompt(state, answers)

        try:
            raw = await self._call_llm(_SAFETY_PROMPT, user_prompt)
            result = self._parse_json(raw)

            if not result.get("safe", True):
                category = result.get("reason_category") or "default"
                refusal_message = await self.generate_refusal_message(
                    category=category, description=state.description
                )
                return {
                    "safe": False,
                    "reason_category": category,
                    "refusal_message": refusal_message,
                    "sector": result.get("sector"),
                    "confidence": result.get("confidence"),
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
            # Keep existing safety behavior: default safe on LLM error
            self.logger.warning(f"[clarifier] check_safety erreur → safe par défaut : {e}")
            return {"safe": True, "sector": None, "confidence": None}

    async def generate_refusal_message(self, category: str, description: str) -> str:
        """
        Génère un message de refus personnalisé via LLM.
        Fallback sur get_refusal_message() si erreur.
        """
        user_prompt = f"Catégorie de refus : {category}\nDescription du projet refusé : {description[:200]}"

        try:
            message = await self._call_llm(_REFUSAL_PROMPT, user_prompt)
            message = message.strip().strip('"').strip("'")
            if message and len(message) > 10:
                self.logger.info(f"[clarifier] refusal message : {message[:100]}")
                return message
        except Exception as e:
            self.logger.warning(f"[clarifier] generate_refusal_message erreur : {e}")

        return get_refusal_message(category)

    async def generate_clarified_idea(self, state: PipelineState, answers: dict | None = None) -> dict:
        """
        Génère le JSON structuré final.
        Appelé UNIQUEMENT si check_safety() → safe: True.
        """
        context = build_idea_summary(
            name=state.name,
            sector=state.sector,
            description=state.description,
            target_audience=state.target_audience,
        )

        answers_block = ""
        if answers:
            answers_block = "\n\nRéponses de clarification :"
            if answers.get("problem"):
                answers_block += f"\n  Problème  : {answers['problem']}"
            if answers.get("target"):
                answers_block += f"\n  Cible     : {answers['target']}"
            if answers.get("solution"):
                answers_block += f"\n  Solution  : {answers['solution']}"

        user_prompt = f"{context}{answers_block}"

        fallback = {
            "type": "clarified",
            "message": "Voici ce que j'ai compris de votre projet.",
            "sector": state.sector or "",
            "target_users": (answers or {}).get("target", ""),
            "problem": (answers or {}).get("problem", ""),
            "solution_description": (answers or {}).get("solution", state.description[:300]),
            "short_pitch": state.name or "",
            "score": 40,
        }

        try:
            raw = await self._call_llm(_CLARIFY_PROMPT, user_prompt)
            result = self._parse_json(raw)

            score = result.get("score", 50)
            try:
                score = int(score)
                score = max(0, min(100, score))
            except (TypeError, ValueError):
                score = 50

            return {
                "type": "clarified",
                "message": result.get("message", ""),
                "sector": result.get("sector", state.sector or ""),
                "target_users": result.get("target_users", ""),
                "problem": result.get("problem", ""),
                "solution_description": result.get("solution_description", ""),
                "short_pitch": result.get("short_pitch", ""),
                "score": score,
            }
        except Exception as e:
            self.logger.warning(f"[clarifier] generate_clarified_idea erreur : {e}")
            return fallback

    async def generate_questions(self, state: PipelineState) -> dict:
        """
        Simplifié :
        - call LLM (QUESTIONS_PROMPT)
        - parse JSON
        - si clarified => directement generate_clarified_idea()
        - si questions => return EXACTLY as-is (NO transformation)
        """
        user_prompt = self._build_user_prompt(state)

        try:
            raw = await self._call_llm(QUESTIONS_PROMPT, user_prompt)
            parsed = self._parse_json(raw)
        except Exception as e:
            self.logger.warning(f"[clarifier] generate_questions erreur → out of service : {e}")
            raise RuntimeError("Service IA indisponible (out of service)")

        result_type = parsed.get("type")

        if result_type == "clarified":
            # REQUIRED: directly call generate_clarified_idea
            return await self.generate_clarified_idea(state)

        if result_type == "questions":
            # REQUIRED: return EXACTLY as-is
            return parsed

        # Unexpected format/type
        raise RuntimeError("Service IA indisponible (out of service)")

    async def run_interactive(self, state: PipelineState, answers: dict | None = None) -> dict:
        """
        Simplifié :
        validation + gibberish + safety + branch (answers ? clarified : questions)
        """
        errors = validate_idea_input(name=state.name or "", description=state.description or "", sector=state.sector or "")
        if errors:
            # Keep existing UX behavior (no axis questions; message only)
            return {
                "type": "questions",
                "message": "Impossible de vous comprendre. Donnez une vraie description claire (2-3 phrases).",
                "missing_axes": [],
                "questions": [],
                "score": 0,
            }

        if is_gibberish(state.description):
            return {
                "type": "questions",
                "message": "Votre saisie ne ressemble pas à une idée réelle. Merci de donner une vraie description claire.",
                "missing_axes": [],
                "questions": [],
                "score": 0,
            }

        # Call safety with/without answers depending on call #1/#2
        safety = await self.check_safety(state, answers)

        if safety.get("sector") and not state.sector:
            state.sector = safety["sector"]

        if not safety["safe"]:
            return {
                "type": "refused",
                "message": safety.get("refusal_message", ""),
                "reason_category": safety.get("reason_category"),
                "score": 0,
                "sector": safety.get("sector", ""),
                "confidence": safety.get("confidence", 0),
            }

        if answers:
            return await self.generate_clarified_idea(state, answers)

        return await self.generate_questions(state)

    # ── Mode batch (LangGraph) — conservé pour ne pas casser le reste du pipeline ──
    async def run(self, state: PipelineState) -> dict:
        self._log_start(state)
        state.current_agent = "idea_clarifier"

        if not state.description or len(state.description.strip()) < 5:
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

        result = await self.generate_clarified_idea(state)
        score = result.get("score", 50)

        clarified = {k: v for k, v in result.items() if k not in ("type", "message")}
        clarified["clarity_score"] = score
        state.clarified_idea = clarified
        state.clarity_score = score
        self._log_success(clarified)

        return {"safe": True, "clarified_idea": clarified, "clarity_score": score}