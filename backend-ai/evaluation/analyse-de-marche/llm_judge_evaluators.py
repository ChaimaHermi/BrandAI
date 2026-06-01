"""
LLM-as-Judge — métriques par agent (analyse de marché).

Prompts judges : voir BLOCK_CONTEXT_COHERENCE_PROMPT et BLOCK_FAITHFULNESS_PROMPT
dans ce fichier (lignes ~30–90).

Azure OpenAI via AZURE_OPENAI_* dans Brand AI/.env (même config que clarification).
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

import config.settings  # noqa: F401

_SCHEMAS_PATH = Path(__file__).parent / "market_schemas.py"
_schemas_spec = importlib.util.spec_from_file_location("market_schemas", _SCHEMAS_PATH)
_schemas_mod = importlib.util.module_from_spec(_schemas_spec)
assert _schemas_spec.loader is not None
_schemas_spec.loader.exec_module(_schemas_mod)

AGENT_LABELS = _schemas_mod.AGENT_LABELS
EVAL_BLOCKS = _schemas_mod.EVAL_BLOCKS
FAITHFULNESS_BLOCKS = _schemas_mod.FAITHFULNESS_BLOCKS
block_collected_sources = _schemas_mod.block_collected_sources

_JUDGE_MODEL: Any = None

# ── Prompts LLM-as-Judge (analyse de marché) ────────────────────────────────

BLOCK_CONTEXT_COHERENCE_PROMPT = """Tu es un évaluateur pour BrandAI (analyse de marché).

Agent évalué : {agent_label}

Idée clarifiée (brief) :
{brief_block}

Sortie de l'agent (bloc JSON) :
{block_block}

Évalue uniquement si CE BLOC reste aligné avec le brief (bon projet, bon secteur, bon pays, bonne cible).
Ne juge pas le format JSON ni la présence de sources — uniquement la cohérence contextuelle.

Score :
1 = parfaitement aligné avec le brief
0.5 = partiellement aligné (écarts mineurs)
0 = hors sujet (mauvais secteur, mauvais pays, autre projet)

Réponds UNIQUEMENT en JSON valide :
{{"score": 0 ou 0.5 ou 1, "justification": "phrase courte"}}"""


BLOCK_FAITHFULNESS_PROMPT = """Tu es un évaluateur pour BrandAI (analyse de marché).

Agent évalué : {agent_label}

CORPUS WEB réellement collecté et fourni à l'agent (snippets, titres, URLs, contenu extrait) :
{collected_block}

Sortie JSON produite par l'agent :
{block_block}

Évalue la fidélité : chaque fait important (chiffre, nom d'entreprise, insight, citation)
doit être explicitement supporté par le CORPUS ci-dessus — pas seulement par une URL
déclarée dans le JSON sans trace dans le texte collecté.

Critères :
- Chiffres : doivent apparaître (ou être clairement déductibles) dans le corpus, sinon null ou score bas
- Insights VOC / tendances : doivent reprendre des formulations ou faits présents dans le corpus
- Concurrents : le nom doit être identifiable dans le corpus ; ne pas accepter une marque inventée
- Si le corpus ne contient pas l'information mais l'agent l'affiche quand même → hallucination

Score :
1 = fidèle au corpus collecté ; pas d'invention majeure
0.5 = quelques affirmations non trouvées ou interprétations douteuses
0 = inventions majeures (chiffres, faits, entités) absentes du corpus

Réponds UNIQUEMENT en JSON valide :
{{"score": 0 ou 0.5 ou 1, "justification": "phrase courte"}}"""


VOC_FAITHFULNESS_PROMPT = """Tu es un évaluateur pour BrandAI (VOC Agent).

CORPUS WEB réellement collecté (snippets, titres, URLs, CONTENT) :
{collected_block}

Sortie JSON VOC produite :
{block_block}

Chaque insight contient "insight" (français), "source" (URL) et "evidence_snippet" (verbatim).

Évalue la fidélité au corpus :
- evidence_snippet DOIT correspondre à un extrait du CONTENT du corpus
- source DOIT être une URL présente dans le corpus
- insight (français) DOIT décrire le même fait que evidence_snippet
  → paraphrase FR d'un corpus EN est ACCEPTÉE si le fait est identique
- user_quotes DOIT être verbatim dans le corpus

Score :
1 = tous les insights restants sont ancrés dans le corpus via evidence_snippet
0.5 = 1–2 insights faibles ou paraphrase douteuse ; sections vides OK
0 = inventions ou snippets absents du corpus

Réponds UNIQUEMENT en JSON valide :
{{"score": 0 ou 0.5 ou 1, "justification": "phrase courte"}}"""


COMPETITOR_FAITHFULNESS_PROMPT = """Tu es un évaluateur pour BrandAI (Competitor Agent).

CORPUS WEB réellement collecté (snippets, titres, URLs, Content) :
{collected_block}

Sortie JSON concurrents produite :
{block_block}

Chaque concurrent contient "name", "website", "evidence_snippet" (verbatim), description (FR).

Évalue la fidélité au corpus :
- evidence_snippet DOIT être un extrait exact du Content du corpus
- name DOIT apparaître dans le corpus (snippet ou titre/content)
- website DOIT être une URL présente dans le corpus (ou vide)
- description / strengths / weaknesses : paraphrase FR acceptée si evidence_snippet ou name prouve le fait
- concurrent inventé (nom absent du corpus, snippet fabriqué) → score bas

Score :
1 = tous les concurrents restants sont ancrés dans le corpus via evidence_snippet ou name explicite
0.5 = 1–2 entrées faibles ; liste vide OK si aucune preuve
0 = inventions majeures ou URLs/noms sans support corpus

Réponds UNIQUEMENT en JSON valide :
{{"score": 0 ou 0.5 ou 1, "justification": "phrase courte"}}"""


STRATEGY_FAITHFULNESS_PROMPT = """Tu es un évaluateur pour BrandAI (analyse stratégique).

Données amont (market, VOC, trends, concurrents) :
{collected_block}

Synthèse stratégique produite (PESTEL, SWOT, demande, insight) :
{block_block}

Évalue si la stratégie reste fidèle aux données amont (pas de statistiques inventées,
pas de concurrents ou faits absents des blocs précédents). Les inférences plausibles
sans chiffre inventé sont acceptables.

Score :
1 = fidèle aux données amont
0.5 = quelques extrapolations douteuses
0 = inventions factuelles majeures

Réponds UNIQUEMENT en JSON valide :
{{"score": 0 ou 0.5 ou 1, "justification": "phrase courte"}}"""


def _resolve_run_outputs(run) -> dict:
    raw = run.outputs or {}
    if not isinstance(raw, dict):
        return {}
    if "market_analysis" in raw or "marketing_plan" in raw or "collected_corpus" in raw:
        return raw
    if len(raw) == 1:
        only = next(iter(raw.values()))
        if isinstance(only, dict):
            return only
    return raw


def _resolve_run_inputs(run, example) -> dict:
    if isinstance(run.inputs, dict):
        if "clarified_idea" in run.inputs:
            return run.inputs
        if len(run.inputs) == 1:
            only = next(iter(run.inputs.values()))
            if isinstance(only, dict) and "clarified_idea" in only:
                return only
    if example and isinstance(example.inputs, dict):
        return example.inputs
    return {}


def _format_brief_block(clarified: dict) -> str:
    fields = (
        ("short_pitch", "Pitch"),
        ("problem", "Problème"),
        ("target_users", "Cible"),
        ("solution_description", "Solution"),
        ("sector", "Secteur"),
        ("country", "Pays"),
        ("country_code", "Code pays"),
        ("budget_min", "Budget min"),
        ("budget_max", "Budget max"),
        ("budget_currency", "Devise"),
    )
    lines = []
    for key, label in fields:
        val = clarified.get(key)
        if val not in (None, ""):
            lines.append(f"{label}: {val}")
    return "\n".join(lines) if lines else "(brief vide)"


def _format_block_json(data: Any, *, max_chars: int = 6_000) -> str:
    if not data:
        return "(bloc vide)"
    try:
        text = json.dumps(data, ensure_ascii=False, indent=0)
    except (TypeError, ValueError):
        text = str(data)
    if len(text) > max_chars:
        return text[:max_chars] + "\n...[tronqué]"
    return text


def _truncate_corpus(text: str, *, max_chars: int = 12_000) -> str:
    text = (text or "").strip()
    if not text:
        return "(corpus vide)"
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[corpus tronqué pour le judge]"


def _faithfulness_collected_block(outputs: dict, block: str, ma: dict) -> str:
    """Corpus web réel si disponible, sinon repli sur sources déclarées dans le JSON."""
    corpus_map = outputs.get("collected_corpus")
    if isinstance(corpus_map, dict):
        raw = corpus_map.get(block)
        if isinstance(raw, str) and raw.strip():
            return _truncate_corpus(raw)
    return block_collected_sources(block, ma if isinstance(ma, dict) else {})


def _get_block_data(outputs: dict, block: str) -> Any:
    if block == "planner":
        return outputs.get("marketing_plan")
    ma = outputs.get("market_analysis") or {}
    if not isinstance(ma, dict):
        return None
    return ma.get(block)


def _pipeline_error(outputs: dict) -> str | None:
    if outputs.get("status") == "error":
        return str(outputs.get("error") or "pipeline error")
    return None


def _get_judge_model():
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
            "Azure OpenAI requis pour les judges : AZURE_OPENAI_ENDPOINT, "
            "AZURE_OPENAI_KEY, AZURE_OPENAI_DEPLOYMENT dans Brand AI/.env"
        )

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


def _make_context_coherence_eval(block: str) -> Callable:
    metric_key = f"{block}_context_coherence"
    agent_label = AGENT_LABELS.get(block, block)

    async def _eval(run, example) -> dict:
        outputs = _resolve_run_outputs(run)
        err = _pipeline_error(outputs)
        if err and block != "planner":
            return {"key": metric_key, "score": None, "comment": f"pipeline: {err}"}

        data = _get_block_data(outputs, block)
        if block == "planner" and not data:
            return {
                "key": metric_key,
                "score": None,
                "comment": "N/A — Marketing Planner hors scope market_eval (pas de marketing_plan)",
            }
        if not data:
            return {"key": metric_key, "score": None, "comment": f"N/A — bloc {block} vide"}

        inputs = _resolve_run_inputs(run, example)
        clarified = inputs.get("clarified_idea") or {}
        prompt = BLOCK_CONTEXT_COHERENCE_PROMPT.format(
            agent_label=agent_label,
            brief_block=_format_brief_block(clarified),
            block_block=_format_block_json(data),
        )
        try:
            score, justification = await _invoke_judge(prompt)
        except Exception as exc:
            return {"key": metric_key, "score": None, "comment": f"judge error: {exc}"}
        if score is None:
            return {"key": metric_key, "score": None, "comment": justification}
        return {"key": metric_key, "score": score, "comment": justification}

    _eval.__name__ = metric_key
    return _eval


def _make_faithfulness_eval(block: str) -> Callable:
    metric_key = f"{block}_faithfulness"
    agent_label = AGENT_LABELS.get(block, block)

    async def _eval(run, example) -> dict:
        outputs = _resolve_run_outputs(run)
        err = _pipeline_error(outputs)
        if err:
            return {"key": metric_key, "score": None, "comment": f"pipeline: {err}"}

        ma = outputs.get("market_analysis") or {}
        data = _get_block_data(outputs, block)
        if not data:
            return {"key": metric_key, "score": None, "comment": f"N/A — bloc {block} vide"}

        if block == "strategy":
            collected = block_collected_sources(block, ma if isinstance(ma, dict) else {})
            block_json = _format_block_json(data)
            prompt = STRATEGY_FAITHFULNESS_PROMPT.format(
                collected_block=collected,
                block_block=block_json,
            )
        elif block == "voc":
            collected = _faithfulness_collected_block(outputs, block, ma)
            block_json = _format_block_json(data)
            prompt = VOC_FAITHFULNESS_PROMPT.format(
                collected_block=collected,
                block_block=block_json,
            )
        elif block == "competitor":
            collected = _faithfulness_collected_block(outputs, block, ma)
            block_json = _format_block_json(data)
            prompt = COMPETITOR_FAITHFULNESS_PROMPT.format(
                collected_block=collected,
                block_block=block_json,
            )
        else:
            collected = _faithfulness_collected_block(outputs, block, ma)
            block_json = _format_block_json(data)
            prompt = BLOCK_FAITHFULNESS_PROMPT.format(
                agent_label=agent_label,
                collected_block=collected,
                block_block=block_json,
            )
        try:
            score, justification = await _invoke_judge(prompt)
        except Exception as exc:
            return {"key": metric_key, "score": None, "comment": f"judge error: {exc}"}
        if score is None:
            return {"key": metric_key, "score": None, "comment": justification}
        return {"key": metric_key, "score": score, "comment": justification}

    _eval.__name__ = metric_key
    return _eval


def build_judge_evaluators() -> list[Callable]:
    """Retourne tous les evaluators LLM (context_coherence + faithfulness par bloc)."""
    evaluators: list[Callable] = []
    evaluators.append(_make_context_coherence_eval("keywords"))
    for block in EVAL_BLOCKS:
        evaluators.append(_make_context_coherence_eval(block))
        evaluators.append(_make_faithfulness_eval(block))
    evaluators.append(_make_context_coherence_eval("planner"))
    return evaluators


def build_voc_judge_evaluators() -> list[Callable]:
    """Judges LLM pour eval VOC seule."""
    return [
        _make_context_coherence_eval("voc"),
        _make_faithfulness_eval("voc"),
    ]


def build_competitor_judge_evaluators() -> list[Callable]:
    """Judges LLM pour eval Competitor seule."""
    return [
        _make_context_coherence_eval("competitor"),
        _make_faithfulness_eval("competitor"),
    ]
