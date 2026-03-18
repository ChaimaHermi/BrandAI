# ══════════════════════════════════════════════════════════════
#  backend-ai/agents/idea_clarifier.py
#  Agent 0 — Idea Clarifier
#
#  RÔLE : Comprendre, valider et structurer l'idée utilisateur.
#
#  FLUX :
#    Appel 1 (sans réponses) :
#      → validate_idea_input() + is_gibberish() — SANS LLM
#      → check_safety()       — sécurité + secteur (LLM)
#      → generate_questions() — 3 questions ciblées (LLM)
#
#    Appel 2 (avec réponses) :
#      → check_safety()            — re-vérification LLM
#                                    analyse description + réponses
#      → generate_clarified_idea() — JSON structuré final (LLM)
#
#  TYPES DE RETOUR :
#    "questions" → 3 champs à remplir
#    "clarified" → JSON final avec score
#    "refused"   → idée non conforme
#
#  CE QUE CET AGENT NE FAIT PAS :
#    - Générer un nom de marque   → Brand Identity Agent
#    - Enrichir stratégiquement   → Idea Enhancer Agent
#    - Analyser la concurrence    → Market Analysis Agent
# ══════════════════════════════════════════════════════════════

import re
import logging

from agents.base_agent import BaseAgent, PipelineState
from guardrails.safety_checks import get_refusal_message
from tools.idea_tools import build_idea_summary, validate_idea_input


logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
#  UTILITAIRE — Détection texte incohérent SANS LLM
# ══════════════════════════════════════════════════════════════

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
    words  = re.findall(r'\w+', text.lower())

    if len(words) < 2:
        return True

    if len(set(words)) == 1:
        return True

    real_words = sum(
        1 for w in words
        if len(w) <= 2 or any(c in vowels for c in w)
    )
    if real_words < 2:
        return True

    for word in words:
        if len(word) > 6:
            ratio = sum(
                1 for c in word if c in vowels
            ) / len(word)
            if ratio < 0.15:
                return True

    return False


# ══════════════════════════════════════════════════════════════
#  PROMPTS
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


_QUESTIONS_PROMPT = """Tu es l'agent Idea Clarifier de BrandAI.

Ton rôle est d'aider un entrepreneur à clarifier son idée
en posant EXACTEMENT 3 questions ciblées.

RÈGLES STRICTES :
- Répondre en français
- Répondre en JSON valide (sans backticks ni markdown)
- Ne jamais répéter un mot deux fois de suite
- Adapter les questions au secteur détecté

QUESTIONS OBLIGATOIRES (dans cet ordre) :
1. Le PROBLÈME concret résolu
2. La CIBLE (qui sont les utilisateurs ?)
3. La SOLUTION (comment ça fonctionne ?)

Reformuler selon le contexte mais garder ce sens.

INTERDIT dans les questions :
- concurrence / différenciation
- business model / pricing
- stratégie marketing

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ADAPTER LE MESSAGE selon la description
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CAS 1 — Description trop courte ou vague :
→ Commencer par expliquer que la description
  n'est pas assez claire.
→ Exemple : "Votre description est un peu courte
  pour que je puisse bien comprendre votre projet.
  Quelques questions vont nous aider à clarifier ça !"

CAS 2 — Description lisible avec sujet identifiable :
→ Message encourageant, mentionner le secteur.
→ Exemple : "Votre idée dans le secteur éducation
  semble prometteuse ! Pour mieux la structurer,
  j'ai besoin de 3 précisions."

FORMAT JSON :
{
  "type": "questions",
  "message": "message adapté selon CAS 1 ou CAS 2",
  "questions": [
    "question sur le problème — adaptée au secteur",
    "question sur la cible — adaptée au secteur",
    "question sur la solution — adaptée au secteur"
  ]
}"""


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
  "target_users": "cible bien définie",
  "problem": "problème clair et reformulé",
  "solution_description": "solution expliquée concrètement",
  "short_pitch": "phrase de 8 à 12 mots maximum",
  "score": nombre entre 0 et 100
}"""


# ══════════════════════════════════════════════════════════════
#  AGENT
# ══════════════════════════════════════════════════════════════

class IdeaClarifierAgent(BaseAgent):
    """
    Agent 0 du pipeline BrandAI.
    Valide, questionne et structure l'idée utilisateur.

    Sécurité :
    - Appel 1 : check_safety() sur description seule
    - Appel 2 : check_safety() sur description + réponses
    Toute la détection est faite par le LLM — pas de hardcode.
    """

    def __init__(self):
        super().__init__(
            agent_name="idea_clarifier",
            temperature=0.3,
            max_retries=3,
        )
        # Groq uniquement — température 0.05 forcée
        self.llm_rotator = self.llm_rotator.groq_only()

    # ── Prompt système ─────────────────────────────────────

    def _build_system_prompt(self, state: PipelineState) -> str:
        return _CLARIFY_PROMPT

    # ── Prompt utilisateur ─────────────────────────────────

    def _build_user_prompt(
        self,
        state: PipelineState,
        answers: dict | None = None,
    ) -> str:
        """
        Construit le prompt envoyé au LLM.
        Si answers présent → séparateurs ━━━ pour
        rendre les réponses très visibles au LLM.
        """
        parts = []

        if state.name and state.name.strip():
            parts.append(f"Nom du projet : {state.name}")

        if state.sector and state.sector.strip():
            parts.append(f"Secteur : {state.sector}")

        parts.append(f"Description : {state.description}")

        if state.target_audience and state.target_audience.strip():
            parts.append(
                f"Public cible mentionné : {state.target_audience}"
            )

        if answers:
            parts.append(
                "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            parts.append(
                "RÉPONSES DE L'UTILISATEUR "
                "— analyser attentivement l'intention :"
            )
            parts.append(
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            if answers.get("problem"):
                parts.append(
                    f"Problème déclaré   : {answers['problem']}"
                )
            if answers.get("target"):
                parts.append(
                    f"Cible déclarée     : {answers['target']}"
                )
            if answers.get("solution"):
                parts.append(
                    f"Solution déclarée  : {answers['solution']}"
                )
            parts.append(
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            parts.append(
                "Question : ces réponses révèlent-elles "
                "une intention illégale ou nuisible ?"
            )

        return "\n".join(parts)

    # ── LLM 1 : Sécurité ──────────────────────────────────

    async def check_safety(
        self,
        state: PipelineState,
        answers: dict | None = None,
    ) -> dict:
        """
        Vérifie la conformité du projet via LLM.

        Appel 1 (answers=None) : analyse description seule
        Appel 2 (answers=...)  : analyse description + réponses
          → les séparateurs ━━━ rendent les réponses
            très visibles pour le LLM

        En cas d'erreur LLM → safe: True par défaut
        (un timeout ne doit pas bloquer l'utilisateur).
        """
        user_prompt = self._build_user_prompt(state, answers)

        try:
            raw    = await self._call_llm(_SAFETY_PROMPT, user_prompt)
            result = self._parse_json(raw)

            self.logger.info(f"[safety] raw : {repr(raw[:200])}")

            if not result.get("safe", True):
                category = result.get("reason_category") or "default"
                self.logger.info(
                    f"[clarifier] Refusé — catégorie : {category}"
                )

                refusal_message = await self.generate_refusal_message(
                    category=category,
                    description=state.description,
                )

                return {
                    "safe":            False,
                    "reason_category": category,
                    "refusal_message": refusal_message,
                    "sector":          result.get("sector"),
                    "confidence":      result.get("confidence"),
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

            return {
                "safe":       True,
                "sector":     sector,
                "confidence": confidence,
            }

        except Exception as e:
            self.logger.warning(
                f"[clarifier] check_safety erreur → "
                f"safe par défaut : {e}"
            )
            return {
                "safe":       True,
                "sector":     None,
                "confidence": None,
            }

    # ── Message de refus personnalisé ─────────────────────

    async def generate_refusal_message(
        self,
        category: str,
        description: str,
    ) -> str:
        """
        Génère un message de refus personnalisé via LLM.
        Mentionne explicitement description + réponses.
        Fallback sur get_refusal_message() si erreur.
        """
        user_prompt = (
            f"Catégorie de refus : {category}\n"
            f"Description du projet refusé : {description[:200]}"
        )

        try:
            message = await self._call_llm(
                _REFUSAL_PROMPT,
                user_prompt,
            )
            message = message.strip().strip('"').strip("'")
            if message and len(message) > 10:
                self.logger.info(
                    f"[clarifier] refusal message : {message[:100]}"
                )
                return message
        except Exception as e:
            self.logger.warning(
                f"[clarifier] generate_refusal_message erreur : {e}"
            )

        return get_refusal_message(category)

    # ── LLM 2a : Questions ────────────────────────────────

    async def generate_questions(
        self,
        state: PipelineState,
    ) -> dict:
        """
        Génère exactement 3 questions ciblées.
        Message adapté selon clarté de la description.
        """
        user_prompt = self._build_user_prompt(state)

        fallback = {
            "type":    "questions",
            "message": "Votre description est un peu courte. "
                       "Quelques questions vont nous aider à "
                       "mieux comprendre votre projet !",
            "questions": [
                "Quel problème concret votre idée résout-elle ?",
                "Pour qui est cette solution ?",
                "Comment fonctionne-t-elle concrètement ?",
            ],
        }

        try:
            raw    = await self._call_llm(_QUESTIONS_PROMPT, user_prompt)
            result = self._parse_json(raw)

            self.logger.info(
                f"[clarifier] questions : {result.get('questions', [])}"
            )

            questions = result.get("questions", [])
            if not questions or len(questions) < 3:
                questions = fallback["questions"]

            return {
                "type":      "questions",
                "message":   result.get("message", fallback["message"]),
                "questions": questions[:3],
            }

        except Exception as e:
            self.logger.warning(
                f"[clarifier] generate_questions erreur : {e}"
            )
            return fallback

    # ── LLM 2b : Clarification ────────────────────────────

    async def generate_clarified_idea(
        self,
        state: PipelineState,
        answers: dict | None = None,
    ) -> dict:
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
            "type":    "clarified",
            "message": "Voici ce que j'ai compris de votre projet.",
            "sector":  state.sector or "",
            "target_users":         (answers or {}).get("target",   ""),
            "problem":              (answers or {}).get("problem",  ""),
            "solution_description": (answers or {}).get(
                "solution", state.description[:300]
            ),
            "short_pitch": state.name or "",
            "score":       40,
        }

        try:
            raw    = await self._call_llm(_CLARIFY_PROMPT, user_prompt)
            result = self._parse_json(raw)

            score = result.get("score", 50)
            try:
                score = int(score)
                score = max(0, min(100, score))
            except (TypeError, ValueError):
                score = 50

            self.logger.info(f"[clarifier] score : {score}")
            self.logger.info(
                f"[clarifier] message : "
                f"{result.get('message', '')[:100]}"
            )

            return {
                "type":    "clarified",
                "message": result.get("message", ""),
                "sector":  result.get("sector", state.sector or ""),
                "target_users":
                    result.get("target_users",         ""),
                "problem":
                    result.get("problem",              ""),
                "solution_description":
                    result.get("solution_description", ""),
                "short_pitch":
                    result.get("short_pitch",          ""),
                "score": score,
            }

        except Exception as e:
            self.logger.warning(
                f"[clarifier] generate_clarified_idea erreur : {e}"
            )
            return fallback

    # ── Point d'entrée principal ──────────────────────────

    async def run_interactive(
        self,
        state: PipelineState,
        answers: dict | None = None,
    ) -> dict:
        """
        Appelé depuis clarifier.py (routes SSE).

        Appel A (answers=None) :
          1. validate_idea_input() — description ≥ 10 chars
          2. is_gibberish()        — filtre SANS LLM
          3. check_safety()        — LLM : sécurité + secteur
          4. generate_questions()  — LLM : 3 questions

        Appel B (answers={problem, target, solution}) :
          1. check_safety(state, answers)
               → LLM analyse description + réponses ensemble
               → Les séparateurs ━━━ rendent les réponses
                 très visibles pour détecter les intentions
               → safe: false → refused avec message LLM
               → safe: true  → generate_clarified_idea()
        """

        # ── Validation basique ────────────────────────────
        errors = validate_idea_input(
            name=state.name or "",
            description=state.description or "",
            sector=state.sector or "",
        )
        if errors:
            return {
                "type":    "questions",
                "message": "Décrivez votre idée pour commencer.",
                "questions": [
                    "Quel problème voulez-vous résoudre ?",
                    "Pour qui est cette solution ?",
                    "Quelle solution proposez-vous ?",
                ],
                "score": 0,
            }

        # ── Gibberish check SANS LLM ──────────────────────
        if is_gibberish(state.description):
            self.logger.info(
                "[clarifier] Gibberish détecté : "
                f"{repr(state.description[:50])}"
            )
            return {
                "type":    "questions",
                "message": "Ce que vous avez saisi ne ressemble "
                           "pas à une description de projet. "
                           "Pouvez-vous décrire votre idée en "
                           "quelques phrases claires ?",
                "questions": [
                    "Quel problème voulez-vous résoudre ?",
                    "Pour qui est cette solution ?",
                    "Quelle solution proposez-vous ?",
                ],
                "score": 0,
            }

        # ── Appel B : avec réponses ───────────────────────
        if answers:

            # LLM analyse description + réponses ensemble
            # Les séparateurs ━━━ dans _build_user_prompt()
            # rendent les réponses très visibles pour le LLM
            safety = await self.check_safety(state, answers)

            if safety.get("sector") and not state.sector:
                state.sector = safety["sector"]

            if not safety["safe"]:
                # Même comportement que l'Appel A refusé
                return {
                    "type":            "refused",
                    "message":         safety.get("refusal_message", ""),
                    "reason_category": safety.get("reason_category"),
                    "score":           0,
                    "sector":          safety.get("sector", ""),
                    "confidence":      safety.get("confidence", 0),
                }

            # safe: True → générer le JSON final
            return await self.generate_clarified_idea(
                state, answers
            )

        # ── Appel A : premier appel sans réponses ─────────
        safety = await self.check_safety(state)

        if safety.get("sector") and not state.sector:
            state.sector = safety["sector"]
            self.logger.info(
                f"[clarifier] secteur propagé : {state.sector}"
            )

        if not safety["safe"]:
            return {
                "type":            "refused",
                "message":         safety.get("refusal_message", ""),
                "reason_category": safety.get("reason_category"),
                "score":           0,
                "sector":          safety.get("sector", ""),
                "confidence":      safety.get("confidence", 0),
            }

        return await self.generate_questions(state)

    # ── Mode batch LangGraph ──────────────────────────────

    async def run(self, state: PipelineState) -> dict:
        """
        Mode batch — appelé par LangGraph.
        Clarification directe sans questions interactives.
        """
        self._log_start(state)
        state.current_agent = "idea_clarifier"

        if not state.description or len(
            state.description.strip()
        ) < 5:
            raise ValueError("Description trop courte")

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