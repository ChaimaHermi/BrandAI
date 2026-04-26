# backend-ai/agents/clarifier/idea_clarifier_agent.py
import re
import logging

from agents.base_agent import BaseAgent, PipelineState
from guardrails.safety_checks import get_refusal_message, check_safety_with_llama_guard
from prompts.clarifier.prompt_idea_clarifier import ANSWER_PROMPT, ANALYSE_PROMPT
from tools.idea_tools import validate_idea_input
logger = logging.getLogger(__name__)


def _answer_value_nonempty(value) -> bool:
    """True if the user provided a non-empty answer (text or numeric budget field)."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (int, float)):
        return True
    return bool(value)


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
        super().__init__(
            agent_name="idea_clarifier",
            temperature=0.3,
            max_retries=3,
            llm_model="openai/gpt-oss-120b",
        )
        self._safety_meta: dict = {}

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
            if answers.get("geography"):
                parts.append(f"Géographie déclarée : {answers['geography']}")
            if answers.get("budget_min"):
                parts.append(f"Budget minimum déclaré : {answers['budget_min']}")
            if answers.get("budget_max"):
                parts.append(f"Budget maximum déclaré : {answers['budget_max']}")
            if answers.get("budget_currency"):
                parts.append(f"Devise déclarée : {answers['budget_currency']}")
            parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        return "\n".join(parts)

    # ─────────────────────────────────────────────────────────
    # Normalisation et validation du résultat LLM
    # ─────────────────────────────────────────────────────────

    def _normalize_result(
        self,
        raw_result: dict,
        state: PipelineState,
        answers: dict | None = None,
    ) -> dict:
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
            valid_axes = {"problem", "target", "solution", "geography", "budget"}
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
            clarified = {
                "type": "clarified",
                "message": (raw_result.get("message") or "").strip(),
                "sector": (raw_result.get("sector") or state.sector or "").strip(),
                "target_users": (raw_result.get("target_users") or "").strip(),
                "problem": (raw_result.get("problem") or "").strip(),
                "solution_description": (raw_result.get("solution_description") or "").strip(),
                "short_pitch": (raw_result.get("short_pitch") or "").strip(),
                "score": score,
                "country": (raw_result.get("country") or "Non précisé").strip(),
                "country_code": (raw_result.get("country_code") or "").strip().upper(),
                "language": (raw_result.get("language") or "fr").strip(),
            }
            clarified = self._ensure_geography_if_needed(clarified)
            if clarified.get("type") == "questions":
                return clarified
            clarified = self._apply_budget_from_answers_if_any(clarified, answers)
            if answers is None:
                return self._ensure_budget_if_needed(clarified)
            return clarified

        # Type inattendu → erreur remontée à la route
        raise RuntimeError(f"[clarifier] type LLM inattendu : {result_type!r}")

    def _ensure_geography_if_needed(self, clarified: dict) -> dict:
        """If geography is missing, convert clarified result into a geography question."""
        country = str(clarified.get("country") or "").strip().lower()
        country_code = str(clarified.get("country_code") or "").strip().upper()

        # Keep behavior simple: if LLM could not provide country, ask user explicitly.
        if country and country not in {"non précisé", "non precise", "nonprecise"}:
            return clarified
        if country_code:
            return clarified

        return {
            "type": "questions",
            "message": (
                "Pour finaliser votre idée, j'ai besoin de la localisation de lancement."
            ),
            "missing_axes": ["geography"],
            "questions": [
                {
                    "axis": "geography",
                    "text": "Dans quel pays ou région souhaitez-vous lancer votre solution ?",
                }
            ],
            "sector": clarified.get("sector", ""),
            "detected_sector": clarified.get("sector", ""),
        }

    def _ensure_budget_if_needed(self, clarified: dict) -> dict:
        """If budget is missing, convert clarified result into a budget question."""
        budget_min = clarified.get("budget_min")
        budget_max = clarified.get("budget_max")
        budget_currency = str(clarified.get("budget_currency") or "").strip().upper()
        has_budget = (
            isinstance(budget_min, (int, float))
            and isinstance(budget_max, (int, float))
            and budget_min > 0
            and budget_max >= budget_min
            and len(budget_currency) >= 3
        )
        if has_budget:
            return clarified

        return {
            "type": "questions",
            "message": (
                "Pour finaliser votre idée, j'ai besoin de votre budget de départ."
            ),
            "missing_axes": ["budget"],
            "questions": [
                {
                    "axis": "budget",
                    "text": "Quel est votre budget de départ (minimum, maximum et devise) ?",
                }
            ],
            "sector": clarified.get("sector", ""),
            "detected_sector": clarified.get("sector", ""),
        }

    def _apply_budget_from_answers_if_any(self, clarified: dict, answers: dict | None) -> dict:
        """Attach normalized budget fields coming from explicit user answers."""
        if not isinstance(answers, dict):
            return clarified
        out = dict(clarified)
        min_raw = answers.get("budget_min")
        max_raw = answers.get("budget_max")
        currency_raw = (answers.get("budget_currency") or "").strip().upper()
        try:
            min_val = float(min_raw) if min_raw not in (None, "") else None
            max_val = float(max_raw) if max_raw not in (None, "") else None
        except (TypeError, ValueError):
            return out
        if min_val is None or max_val is None:
            return out
        if min_val <= 0 or max_val < min_val:
            return out
        if len(currency_raw) < 3:
            return out
        out["budget_min"] = min_val
        out["budget_max"] = max_val
        out["budget_currency"] = currency_raw
        return out

    async def _run_safety_gate(self, payload: dict) -> dict | None:
        """
        Run external safety gate with graceful fallback.
        Returns refused payload if blocked, else None.
        """
        try:
            safety = await check_safety_with_llama_guard(payload)
            self._safety_meta = {
                "enabled": True,
                "provider": safety.get("provider", "nvidia"),
                "model": safety.get("model", ""),
                "status": "safe" if safety.get("safe", True) else "blocked",
                "fallback_used": False,
                "reason_category": safety.get("reason_category"),
            }
        except Exception as exc:
            # Do not block product flow if safety service is temporarily unavailable.
            self.logger.warning("[clarifier] safety gate unavailable, fallback to main LLM path: %s", exc)
            self._safety_meta = {
                "enabled": True,
                "provider": "nvidia",
                "model": "",
                "status": "unavailable",
                "fallback_used": True,
                "reason_category": None,
            }
            return None

        if safety.get("safe", True):
            return None

        reason_category = safety.get("reason_category") or "default"
        return {
            "type": "refused",
            "reason_category": reason_category,
            "message": get_refusal_message(reason_category),
            "sector": "",
            "score": 0,
        }

    def _attach_safety_meta(self, result: dict) -> dict:
        enriched = dict(result)
        if self._safety_meta:
            enriched["safety"] = self._safety_meta
        return enriched

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

        safety_block = await self._run_safety_gate(
            {
                "stage": "clarifier_input",
                "name": state.name or "",
                "sector": state.sector or "",
                "description": state.description or "",
                "target_audience": state.target_audience or "",
            }
        )
        if safety_block:
            return self._attach_safety_meta(safety_block)

        # ── 1 LLM call : sécurité + analyse ──────────────────
        user_prompt = self._build_context(state)

        try:
            raw = await self._call_llm(ANALYSE_PROMPT, user_prompt)
            result = self._parse_json(raw)
        except Exception as e:
            self.logger.error(f"[clarifier] run_start LLM error : {e}")
            raise RuntimeError("Service IA indisponible. Réessayez dans quelques instants.")

        normalized = self._normalize_result(result, state, answers=None)

        # Propager le secteur détecté dans le state pour le 2ème appel
        if normalized.get("sector") and not state.sector:
            state.sector = normalized["sector"]

        # Ajouter detected_sector pour que le frontend le renvoie au 2ème appel
        normalized["detected_sector"] = normalized.get("sector", "")

        self.logger.info(f"[clarifier] run_start → type={normalized['type']}")
        return self._attach_safety_meta(normalized)

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
        if not answers or not any(_answer_value_nonempty(v) for v in answers.values()):
            raise ValueError("Aucune réponse fournie.")

        safety_block = await self._run_safety_gate(
            {
                "stage": "clarifier_answers",
                "name": state.name or "",
                "sector": state.sector or "",
                "description": state.description or "",
                "target_audience": state.target_audience or "",
                "answers": answers,
            }
        )
        if safety_block:
            return self._attach_safety_meta(safety_block)

        # ── 1 LLM call : sécurité sur réponses + structuration ──
        user_prompt = self._build_context(state, answers)

        try:
            raw = await self._call_llm(ANSWER_PROMPT, user_prompt)
            result = self._parse_json(raw)
        except Exception as e:
            self.logger.error(f"[clarifier] run_answer LLM error : {e}")
            raise RuntimeError("Service IA indisponible. Réessayez dans quelques instants.")

        normalized = self._normalize_result(result, state, answers=answers)

        # Propager le secteur si enrichi
        if normalized.get("sector") and not state.sector:
            state.sector = normalized["sector"]

        self.logger.info(f"[clarifier] run_answer → type={normalized['type']}, score={normalized.get('score', 0)}")
        return self._attach_safety_meta(normalized)

    # ─────────────────────────────────────────────────────────
    # Compatibilité — méthodes conservées pour la route existante
    # ─────────────────────────────────────────────────────────

    async def run_interactive(self, state: PipelineState, answers: dict | None = None) -> dict:
        """
        Point d'entrée unique appelé par la route clarifier.py.
        Délègue vers run_start() ou run_answer() selon le contexte.
        Conservé pour ne pas modifier la route.
        """
        if answers and any(_answer_value_nonempty(v) for v in answers.values()):
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
            clarified.setdefault("country", "Non précisé")
            clarified.setdefault("country_code", "")
            clarified.setdefault("language", "fr")
            clarified["clarity_score"] = score
            state.clarified_idea = clarified
            state.clarity_score = score
            self._log_success(clarified)
            return {"safe": True, "clarified_idea": clarified, "clarity_score": score}

        # type = "questions" → pipeline batch ne peut pas continuer
        raise RuntimeError("[clarifier] Idée incomplète, questions nécessaires.")