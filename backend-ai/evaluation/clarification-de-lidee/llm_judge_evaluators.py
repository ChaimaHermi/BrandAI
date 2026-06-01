"""LLM-as-Judge — questions_relevance et brief_coherence (epic clarification)."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import config.settings  # noqa: F401

_JUDGE_MODEL: Any = None

QUESTIONS_RELEVANCE_PROMPT = """Tu es un évaluateur pour BrandAI (clarification d'idée).

Idée initiale :
{description}

Contexte : nom={name}, secteur saisi={sector_input}, cible mentionnée={target_audience}
Type de sortie agent : {output_type}
Message agent : {agent_message}

Questions générées :
{questions_block}

Évalue uniquement la pertinence des questions par rapport à l'idée initiale.
Critères :
- Les questions ciblent des axes réellement manquants ou flous (problem, target, solution, geography, budget).
- Pas de questions hors sujet (marketing, concurrence, business model interdits sauf budget).
- Formulation claire et utile pour faire avancer l'utilisateur.

Score :
1 = questions pertinentes et bien ciblées
0.5 = partiellement pertinentes ou trop génériques
0 = hors sujet, inutiles ou incohérentes avec l'idée

Réponds UNIQUEMENT en JSON valide :
{{"score": 0 ou 0.5 ou 1, "justification": "phrase courte"}}"""


BRIEF_COHERENCE_PROMPT = """Tu es un évaluateur pour BrandAI (clarification d'idée).

Idée initiale :
{description}

Contexte : nom={name}, secteur saisi={sector_input}, cible mentionnée={target_audience}
Type attendu (référence dataset) : {expected_type}

Brief clarifié généré :
{brief_block}

Évalue uniquement la cohérence du brief clarifié.
Critères :
- Respecte l'idée initiale (pas d'invention majeure).
- Ne change pas secteur, cible ou solution de façon contradictoire.
- Pas d'informations contradictoires ou ajouts non présents dans l'entrée.
- Structure exploitable (problème, cible, solution, géographie, proposition de valeur).
- Exploitable pour l'analyse de marché.

Score :
1 = cohérent, complet et exploitable
0.5 = partiellement cohérent ou partiellement exploitable
0 = incohérent, contradictoire ou inexploitable

Réponds UNIQUEMENT en JSON valide :
{{"score": 0 ou 0.5 ou 1, "justification": "phrase courte"}}"""


def _resolve_run_outputs(run) -> dict:
    raw = run.outputs or {}
    if not isinstance(raw, dict):
        return {}
    if "type" in raw:
        return raw
    if len(raw) == 1:
        only = next(iter(raw.values()))
        if isinstance(only, dict) and "type" in only:
            return only
    return raw


def _resolve_run_inputs(run, example) -> dict:
    if isinstance(run.inputs, dict):
        if "description" in run.inputs:
            return run.inputs
        if len(run.inputs) == 1:
            only = next(iter(run.inputs.values()))
            if isinstance(only, dict) and "description" in only:
                return only
    if example and isinstance(example.inputs, dict):
        return example.inputs
    return {}


def _format_questions_block(outputs: dict) -> str:
    lines: list[str] = []
    for q in outputs.get("questions") or []:
        if isinstance(q, dict) and q.get("text"):
            lines.append(f"- [{q.get('axis', '?')}] {q['text']}")
    missing = outputs.get("missing_axes") or []
    if missing:
        lines.append(f"Axes manquants déclarés : {', '.join(missing)}")
    return "\n".join(lines) if lines else "(aucune question structurée)"


def _format_brief_block(outputs: dict) -> str:
    fields = (
        ("sector", "Secteur"),
        ("problem", "Problème"),
        ("target_users", "Cible"),
        ("solution_description", "Solution"),
        ("short_pitch", "Pitch"),
        ("country", "Pays"),
        ("country_code", "Code pays"),
        ("budget_min", "Budget min"),
        ("budget_max", "Budget max"),
        ("budget_currency", "Devise"),
        ("score", "Score clarté"),
        ("message", "Message"),
    )
    lines = [f"Type: {outputs.get('type', '')}"]
    for key, label in fields:
        val = outputs.get(key)
        if val not in (None, ""):
            lines.append(f"{label}: {val}")
    return "\n".join(lines)


def _get_judge_model():
    """Judge LLM — Azure OpenAI uniquement (AZURE_OPENAI_* dans Brand AI/.env)."""
    global _JUDGE_MODEL
    if _JUDGE_MODEL is not None:
        return _JUDGE_MODEL
    from langchain_openai import AzureChatOpenAI

    endpoint = (config.settings.AZURE_OPENAI_ENDPOINT or "").strip().rstrip("/")
    api_key = (config.settings.AZURE_OPENAI_KEY or "").strip()
    deployment = (
        os.getenv("LANGCHAIN_EVAL_JUDGE_DEPLOYMENT")
        or config.settings.AZURE_OPENAI_DEPLOYMENT
        or ""
    ).strip()
    api_version = (config.settings.AZURE_OPENAI_API_VERSION or "").strip()

    if not endpoint or not api_key or not deployment:
        raise RuntimeError(
            "Azure OpenAI requis pour les judges : renseigner AZURE_OPENAI_ENDPOINT, "
            "AZURE_OPENAI_KEY et AZURE_OPENAI_DEPLOYMENT dans Brand AI/.env"
        )

    # Ne pas passer par api.openai.com : endpoint + deployment Azure obligatoires.
    _JUDGE_MODEL = AzureChatOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        azure_deployment=deployment,
        api_version=api_version,
        model=deployment,
        temperature=0,
        max_tokens=800,
        max_retries=2,
    )
    return _JUDGE_MODEL


def _parse_judge_json(text: str) -> tuple[float | None, str]:
    text = (text or "").strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[^{}]*\"score\"[^{}]*\}", text, re.DOTALL)
        if not match:
            return None, f"JSON invalide: {text[:200]}"
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None, f"JSON invalide: {text[:200]}"
    score = data.get("score")
    justification = str(data.get("justification") or data.get("explanation") or "")
    try:
        score_f = float(score)
    except (TypeError, ValueError):
        return None, justification or "score manquant"
    if score_f not in (0.0, 0.5, 1.0):
        return None, justification or f"score hors plage: {score_f}"
    return score_f, justification


async def _invoke_judge(prompt: str) -> tuple[float | None, str]:
    model = _get_judge_model()
    response = await model.ainvoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)
    return _parse_judge_json(content)


async def eval_questions_relevance(run, example) -> dict:
    outputs = _resolve_run_outputs(run)
    if outputs.get("type") != "questions":
        return {
            "key": "questions_relevance",
            "score": None,
            "comment": "N/A — type != questions",
        }
    inputs = _resolve_run_inputs(run, example)
    prompt = QUESTIONS_RELEVANCE_PROMPT.format(
        description=inputs.get("description", ""),
        name=inputs.get("name") or "(non renseigné)",
        sector_input=inputs.get("sector") or "(non renseigné)",
        target_audience=inputs.get("target_audience") or "(non renseigné)",
        output_type=outputs.get("type", ""),
        agent_message=outputs.get("message", ""),
        questions_block=_format_questions_block(outputs),
    )
    try:
        score, justification = await _invoke_judge(prompt)
    except Exception as exc:
        return {
            "key": "questions_relevance",
            "score": None,
            "comment": f"judge error: {exc}",
        }
    if score is None:
        return {
            "key": "questions_relevance",
            "score": None,
            "comment": justification,
        }
    return {
        "key": "questions_relevance",
        "score": score,
        "comment": justification,
    }


async def eval_brief_coherence(run, example) -> dict:
    outputs = _resolve_run_outputs(run)
    if outputs.get("type") != "clarified":
        return {
            "key": "brief_coherence",
            "score": None,
            "comment": "N/A — type != clarified",
        }
    inputs = _resolve_run_inputs(run, example)
    expected = (example.outputs or {}).get("expected_type", "") if example else ""
    prompt = BRIEF_COHERENCE_PROMPT.format(
        description=inputs.get("description", ""),
        name=inputs.get("name") or "(non renseigné)",
        sector_input=inputs.get("sector") or "(non renseigné)",
        target_audience=inputs.get("target_audience") or "(non renseigné)",
        expected_type=expected,
        brief_block=_format_brief_block(outputs),
    )
    try:
        score, justification = await _invoke_judge(prompt)
    except Exception as exc:
        return {
            "key": "brief_coherence",
            "score": None,
            "comment": f"judge error: {exc}",
        }
    if score is None:
        return {
            "key": "brief_coherence",
            "score": None,
            "comment": justification,
        }
    return {
        "key": "brief_coherence",
        "score": score,
        "comment": justification,
    }
