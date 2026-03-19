# backend-ai/agents/idea_clarifier.py
import re
import logging

from agents.base_agent import BaseAgent, PipelineState
from guardrails.safety_checks import get_refusal_message
from tools.idea_tools import validate_idea_input

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# UTILITAIRE — Détection texte incohérent SANS LLM
# ══════════════════════════════════════════════════════════════
def is_gibberish(text: str) -> bool:
    if not text or len(text.strip()) < 10:
        return True

    vowels = set("aeiouyàâéèêëîïôùûüœ")
    words = re.findall(r"\w+", text.lower())

    if len(words) < 2:
        return True

    # Tous les mots identiques : "test test test test"
    if len(set(words)) == 1:
        return True

    # Quasi-répétition : plus de 70% des mots sont identiques
    # "test tes tes test test" → 5 mots, "test" apparaît 3 fois = 60%
    # On abaisse le seuil à 60% pour attraper ce cas
    from collections import Counter
    most_common_count = Counter(words).most_common(1)[0][1]
    if len(words) >= 3 and most_common_count / len(words) >= 0.60:
        return True

    # Vocabulaire trop pauvre : moins de 3 mots distincts pour 5+ mots
    if len(words) >= 5 and len(set(words)) <= 2:
        return True

    real_words = sum(
        1 for w in words
        if len(w) <= 3 or (
            any(c in vowels for c in w) and
            sum(1 for c in w if c in vowels) / len(w) >= 0.20
        )
    )
    if real_words < 2:
        return True

    # Séquences de consonnes anormalement longues
    for word in words:
        if len(word) < 5:
            continue
        max_consonant_streak = 0
        streak = 0
        for c in word:
            if c not in vowels:
                streak += 1
                max_consonant_streak = max(max_consonant_streak, streak)
            else:
                streak = 0
        if max_consonant_streak > 4:
            return True

    return False

# ══════════════════════════════════════════════════════════════
# PROMPT 1 — Analyse initiale (description seule)
# Fait tout en 1 call : sécurité + axes + questions ou clarified
# ══════════════════════════════════════════════════════════════
_ANALYSE_PROMPT = """Tu es l'agent Idea Clarifier de BrandAI.

Ta mission en UN SEUL appel :
1. Vérifier si le projet est safe (légal, non nuisible)
2. Si safe → analyser si les 3 axes sont présents
3. Retourner le bon type de réponse

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ÉTAPE 1 — SÉCURITÉ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Refuser si l'intention est CLAIREMENT :
- Tromper / escroquer des personnes (fraud)
- Activités illégales : drogues, armes, faux documents, piratage (illegal)
- Contenu nuisible, violent, dangereux (harmful)
- Exploitation de mineurs (harmful)

Règles de sécurité :
- Cybersécurité défensive ≠ hacking malveillant
- Crypto légal ≠ arnaque
- Projet flou sans intention claire → safe
- Juger l'INTENTION RÉELLE, pas les mots isolés
- En cas de doute → safe

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ÉTAPE 2 — ANALYSE DES 3 AXES (si safe)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Une idée est CLAIRE si ces 3 éléments sont présents et précis :
1. PROBLÈME — quel problème concret est résolu ?
2. CIBLE    — qui sont les utilisateurs ?
3. SOLUTION — comment fonctionne la solution ?

Considérer comme "non clair" si : trop vague, trop général, implicite, ambigu, absent.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTERDIT dans les questions :
concurrence, différenciation, business model, pricing, marketing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMATS DE RÉPONSE (JSON strict, sans backticks)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CAS 1 — PROJET REFUSÉ :
{
  "type": "refused",
  "reason_category": "fraud" | "illegal" | "harmful",
  "message": "Message professionnel en français expliquant le refus (3 phrases max). Phrase 1 : raison basée sur la description. Phrase 2 : pourquoi BrandAI ne peut pas accompagner. Phrase 3 : invitation à soumettre un projet légal.",
  "sector": "secteur détecté ou null"
}

CAS 2 — AXES MANQUANTS (questions nécessaires) :
{
  "type": "questions",
  "message": "Message court et naturel en français (1-2 phrases)",
  "missing_axes": ["problem"] | ["target"] | ["solution"] | combinaison,
  "questions": [
    {"axis": "problem" | "target" | "solution", "text": "Question courte et précise"}
  ],
  "sector": "secteur détecté"
}

CAS 3 — IDÉE CLAIRE (tous les axes présents) :
{
  "type": "clarified",
  "message": "1-2 phrases naturelles et encourageantes en français",
  "sector": "secteur détecté",
  "target_users": "cible définie précisément",
  "problem": "problème reformulé clairement",
  "solution_description": "solution expliquée concrètement",
  "short_pitch": "phrase de 8 à 12 mots maximum",
  "score": nombre entre 80 et 100
}

RÈGLES ABSOLUES :
- Répondre UNIQUEMENT en JSON valide
- Pas de texte avant ou après le JSON
- Pas de backticks ni de markdown
- Répondre en français dans les champs message/text
- Ne jamais inventer d'informations absentes
- missing_axes ne contient QUE les axes réellement absents ou ambigus
- Maximum 3 questions
"""


# ══════════════════════════════════════════════════════════════
# PROMPT 2 — Analyse des réponses utilisateur
# Fait tout en 1 call : sécurité sur réponses + structuration finale
# ══════════════════════════════════════════════════════════════
_ANSWER_PROMPT = """Tu es l'agent Idea Clarifier de BrandAI.

L'utilisateur a répondu aux questions de clarification.
Ta mission en UN SEUL appel :
1. Vérifier si les RÉPONSES révèlent une intention illégale ou nuisible
2. Si safe → construire l'idée clarifiée complète

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RÈGLE CRITIQUE DE SÉCURITÉ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Analyser l'ENSEMBLE description originale + réponses.
Une description innocente avec des réponses malveillantes = REFUSÉ.

Exemples :
- Description "marketplace" + réponse "vente de drogue" → refused / illegal
- Description "app mobile" + réponse "escroquer des retraités" → refused / fraud
- Description "marketplace" + réponse "vêtements pour enfants" → clarified

Refuser si l'intention révélée est :
- fraud   : tromper / escroquer des personnes
- illegal : drogues, armes, faux documents, piratage
- harmful : contenu nuisible, violent, exploitation de mineurs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SI SAFE → STRUCTURATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Construire une idée claire à partir de la description + réponses.
Ne jamais inventer d'informations non fournies.
Ne jamais proposer de stratégie ou business model.

SCORING :
- problème clair    : +33 pts
- cible claire      : +33 pts
- solution claire   : +34 pts
Score 80-100 = idée prête pour le pipeline

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMATS DE RÉPONSE (JSON strict, sans backticks)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CAS 1 — RÉPONSES REFUSÉES :
{
  "type": "refused",
  "reason_category": "fraud" | "illegal" | "harmful",
  "message": "Message professionnel en français expliquant le refus (3 phrases max). Baser sur la description ET les réponses fournies.",
  "sector": "secteur détecté ou null"
}

CAS 2 — IDÉE CLARIFIÉE :
{
  "type": "clarified",
  "message": "1-2 phrases naturelles et encourageantes en français",
  "sector": "secteur détecté",
  "target_users": "cible définie précisément",
  "problem": "problème reformulé clairement",
  "solution_description": "solution expliquée concrètement",
  "short_pitch": "phrase de 8 à 12 mots maximum",
  "score": nombre entre 0 et 100
}

RÈGLES ABSOLUES :
- Répondre UNIQUEMENT en JSON valide
- Pas de texte avant ou après le JSON
- Pas de backticks ni de markdown
- Répondre en français dans les champs message
- Ne jamais reformuler une activité illégale comme légale
"""


# ══════════════════════════════════════════════════════════════
# AGENT
# ══════════════════════════════════════════════════════════════
class IdeaClarifierAgent(BaseAgent):
    """
    Agent 0 du pipeline BrandAI.

    Flux simplifié — 2 LLM calls maximum :

    Appel 1 — run_start() :
        description → sécurité + analyse axes → refused | questions | clarified

    Appel 2 — run_answer() :
        description + réponses → sécurité sur réponses + structuration → refused | clarified
    """

    def __init__(self):
        super().__init__(agent_name="idea_clarifier", temperature=0.3, max_retries=3)
        self.llm_rotator = self.llm_rotator.groq_only()

    # ─────────────────────────────────────────────────────────
    # Construction du contexte utilisateur
    # ─────────────────────────────────────────────────────────

    def _build_context(self, state: PipelineState, answers: dict | None = None) -> str:
        """
        Construit le bloc de contexte injecté dans le user prompt.
        Toujours : nom (si dispo) + secteur (si dispo) + description.
        Si answers fournis : ajoute les réponses avec séparateurs visuels.
        """
        parts = []

        if state.name and state.name.strip():
            parts.append(f"Nom du projet : {state.name.strip()}")

        if state.sector and state.sector.strip():
            parts.append(f"Secteur : {state.sector.strip()}")

        parts.append(f"Description : {state.description.strip()}")

        if state.target_audience and state.target_audience.strip():
            parts.append(f"Public cible mentionné : {state.target_audience.strip()}")

        if answers:
            parts.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            parts.append("RÉPONSES DE L'UTILISATEUR :")
            parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            if answers.get("problem"):
                parts.append(f"Problème déclaré  : {answers['problem']}")
            if answers.get("target"):
                parts.append(f"Cible déclarée    : {answers['target']}")
            if answers.get("solution"):
                parts.append(f"Solution déclarée : {answers['solution']}")
            parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        return "\n".join(parts)

    # ─────────────────────────────────────────────────────────
    # Normalisation et validation du résultat LLM
    # ─────────────────────────────────────────────────────────

    def _normalize_result(self, raw_result: dict, state: PipelineState) -> dict:
        """
        Normalise et valide le JSON retourné par le LLM.
        Garantit que tous les champs attendus sont présents et typés.
        """
        result_type = raw_result.get("type")

        if result_type == "refused":
            return {
                "type": "refused",
                "reason_category": raw_result.get("reason_category") or "default",
                "message": (raw_result.get("message") or "").strip()
                           or get_refusal_message("default"),
                "sector": (raw_result.get("sector") or state.sector or "").strip(),
                "score": 0,
            }

        if result_type == "questions":
            questions = raw_result.get("questions") or []
            missing_axes = raw_result.get("missing_axes") or []
            # Sécurité : garantir la cohérence questions / missing_axes
            valid_axes = {"problem", "target", "solution"}
            questions = [
                q for q in questions
                if isinstance(q, dict)
                and q.get("axis") in valid_axes
                and q.get("text", "").strip()
            ]
            missing_axes = [a for a in missing_axes if a in valid_axes]
            return {
                "type": "questions",
                "message": (raw_result.get("message") or "").strip(),
                "missing_axes": missing_axes,
                "questions": questions,
                "sector": (raw_result.get("sector") or state.sector or "").strip(),
                "detected_sector": (raw_result.get("sector") or state.sector or "").strip(),
            }

        if result_type == "clarified":
            score = raw_result.get("score", 50)
            try:
                score = int(score)
                score = max(0, min(100, score))
            except (TypeError, ValueError):
                score = 50
            return {
                "type": "clarified",
                "message": (raw_result.get("message") or "").strip(),
                "sector": (raw_result.get("sector") or state.sector or "").strip(),
                "target_users": (raw_result.get("target_users") or "").strip(),
                "problem": (raw_result.get("problem") or "").strip(),
                "solution_description": (raw_result.get("solution_description") or "").strip(),
                "short_pitch": (raw_result.get("short_pitch") or "").strip(),
                "score": score,
            }

        # Type inattendu → erreur remontée à la route
        raise RuntimeError(f"[clarifier] type LLM inattendu : {result_type!r}")

    # ─────────────────────────────────────────────────────────
    # Méthode 1 — Appel initial (description seule)
    # ─────────────────────────────────────────────────────────

    async def run_start(self, state: PipelineState) -> dict:
        """
        1er appel — déclenché quand l'utilisateur soumet son idée.

        Pipeline interne (1 seul LLM call) :
          - Filtre gibberish sans LLM
          - LLM : sécurité + analyse axes → refused | questions | clarified

        Retourne un dict avec type = "refused" | "questions" | "clarified"
        """
        # ── Validation locale sans LLM ────────────────────────
        errors = validate_idea_input(
            name=state.name or "",
            description=state.description or "",
            sector=state.sector or "",
        )
        if errors:
            return {
                "type": "questions",
                "message": "Merci de fournir une description plus détaillée de votre projet (2-3 phrases minimum).",
                "missing_axes": [],
                "questions": [],
                "sector": "",
                "detected_sector": "",
            }

        if is_gibberish(state.description):
            return {
                "type": "questions",
                "message": "Votre saisie ne ressemble pas à une idée réelle. Merci de décrire votre projet en quelques phrases.",
                "missing_axes": [],
                "questions": [],
                "sector": "",
                "detected_sector": "",
            }

        # ── 1 LLM call : sécurité + analyse ──────────────────
        user_prompt = self._build_context(state)

        try:
            raw = await self._call_llm(_ANALYSE_PROMPT, user_prompt)
            result = self._parse_json(raw)
        except Exception as e:
            self.logger.error(f"[clarifier] run_start LLM error : {e}")
            raise RuntimeError("Service IA indisponible. Réessayez dans quelques instants.")

        normalized = self._normalize_result(result, state)

        # Propager le secteur détecté dans le state pour le 2ème appel
        if normalized.get("sector") and not state.sector:
            state.sector = normalized["sector"]

        # Ajouter detected_sector pour que le frontend le renvoie au 2ème appel
        normalized["detected_sector"] = normalized.get("sector", "")

        self.logger.info(f"[clarifier] run_start → type={normalized['type']}")
        return normalized

    # ─────────────────────────────────────────────────────────
    # Méthode 2 — Appel après réponses utilisateur
    # ─────────────────────────────────────────────────────────

    async def run_answer(self, state: PipelineState, answers: dict) -> dict:
        """
        2ème appel — déclenché quand l'utilisateur répond aux questions.

        Pipeline interne (1 seul LLM call) :
          - LLM : sécurité sur réponses + structuration → refused | clarified

        answers = {"problem": "...", "target": "...", "solution": "..."}
        (les clés absentes des questions posées sont ignorées)

        Retourne un dict avec type = "refused" | "clarified"
        """
        if not answers or not any(v and v.strip() for v in answers.values()):
            raise ValueError("Aucune réponse fournie.")

        # ── 1 LLM call : sécurité sur réponses + structuration ──
        user_prompt = self._build_context(state, answers)

        try:
            raw = await self._call_llm(_ANSWER_PROMPT, user_prompt)
            result = self._parse_json(raw)
        except Exception as e:
            self.logger.error(f"[clarifier] run_answer LLM error : {e}")
            raise RuntimeError("Service IA indisponible. Réessayez dans quelques instants.")

        normalized = self._normalize_result(result, state)

        # Propager le secteur si enrichi
        if normalized.get("sector") and not state.sector:
            state.sector = normalized["sector"]

        self.logger.info(f"[clarifier] run_answer → type={normalized['type']}, score={normalized.get('score', 0)}")
        return normalized

    # ─────────────────────────────────────────────────────────
    # Compatibilité — méthodes conservées pour la route existante
    # ─────────────────────────────────────────────────────────

    async def run_interactive(self, state: PipelineState, answers: dict | None = None) -> dict:
        """
        Point d'entrée unique appelé par la route clarifier.py.
        Délègue vers run_start() ou run_answer() selon le contexte.
        Conservé pour ne pas modifier la route.
        """
        if answers and any(v and v.strip() for v in answers.values()):
            return await self.run_answer(state, answers)
        return await self.run_start(state)

    # ── Mode batch LangGraph — conservé pour ne pas casser le pipeline ──
    async def run(self, state: PipelineState) -> dict:
        self._log_start(state)
        state.current_agent = "idea_clarifier"

        if not state.description or len(state.description.strip()) < 5:
            raise ValueError("Description trop courte")

        result = await self.run_start(state)

        if result["type"] == "refused":
            state.status = "refused"
            return {
                "safe": False,
                "reason_category": result.get("reason_category"),
                "refusal_message": result.get("message"),
                "clarified_idea": {},
                "clarity_score": 0,
            }

        if result["type"] == "clarified":
            score = result.get("score", 50)
            clarified = {k: v for k, v in result.items() if k not in ("type", "message", "detected_sector")}
            clarified["clarity_score"] = score
            state.clarified_idea = clarified
            state.clarity_score = score
            self._log_success(clarified)
            return {"safe": True, "clarified_idea": clarified, "clarity_score": score}

        # type = "questions" → pipeline batch ne peut pas continuer
        raise RuntimeError("[clarifier] Idée incomplète, questions nécessaires.")