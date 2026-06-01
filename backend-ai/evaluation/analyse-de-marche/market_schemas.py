"""Schémas déterministes — format_compliance (analyse de marché)."""

from __future__ import annotations

import json
from typing import Any

# Blocs évalués (clé dans market_analysis ou sortie planner)
EVAL_BLOCKS = ("market", "competitor", "voc", "trends", "strategy")
ALL_EVAL_BLOCKS = ("keywords",) + EVAL_BLOCKS

AGENT_LABELS: dict[str, str] = {
    "keywords": "Idea Keyword Extractor",
    "market": "Market Sizing Agent",
    "competitor": "Competitor Agent",
    "voc": "VOC Agent",
    "trends": "Trends & Risks Agent",
    "strategy": "Analyse stratégique",
    "planner": "Marketing Planner",
}

# Champs obligatoires pour format_compliance (présence + type)
FORMAT_FIELDS: dict[str, list[str]] = {
    "keywords": [
        "primary_keywords",
        "market_keywords",
        "sector_growth_keywords",
        "competitor_queries",
        "voc_keywords",
        "trend_keywords",
        "risk_keywords",
    ],
    "market": [
        "market_size",
        "CAGR",
        "market_signals",
        "sources",
    ],
    "voc": [
        "pain_points",
        "frustrations",
        "desired_features",
        "market_insights",
        "sources",
    ],
    "competitor": ["competitors"],
    "trends": [
        "market_trends",
        "risks",
        "opportunities",
        "sources",
    ],
    "strategy": [
        "pestel",
        "swot",
        "demand_analysis",
        "strategic_insight",
    ],
    "planner": [
        "positioning",
        "messaging",
        "channels",
        "content_strategy",
        "budget_allocation",
        "go_to_market",
        "action_plan",
    ],
}

# Sections comptées pour section_completeness (doivent être « remplies »)
SECTION_FIELDS: dict[str, list[str]] = {
    "keywords": [
        "primary_keywords",
        "market_keywords",
        "competitor_queries",
        "voc_keywords",
        "trend_keywords",
        "risk_keywords",
    ],
    "market": ["market_size", "CAGR", "market_signals", "sources"],
    "voc": [
        "pain_points",
        "frustrations",
        "desired_features",
        "market_insights",
        "sources",
    ],
    "competitor": ["competitors"],
    "trends": ["market_trends", "risks", "opportunities", "sources"],
    "strategy": ["pestel", "swot", "demand_analysis", "strategic_insight"],
    "planner": ["positioning", "messaging", "channels", "go_to_market", "action_plan"],
}

# Agents avec métrique faithfulness (recherche web)
FAITHFULNESS_BLOCKS = frozenset({"market", "competitor", "voc", "trends", "strategy"})

# Métriques LangSmith par préfixe de bloc
def metric_keys_for_block(prefix: str, *, with_faithfulness: bool) -> tuple[str, ...]:
    keys = (
        f"{prefix}_format_compliance",
        f"{prefix}_context_coherence",
    )
    if with_faithfulness:
        return keys + (f"{prefix}_faithfulness",)
    return keys


def all_report_metrics() -> tuple[str, ...]:
    out: list[str] = []
    out.extend(metric_keys_for_block("keywords", with_faithfulness=False))
    for block in EVAL_BLOCKS:
        out.extend(metric_keys_for_block(block, with_faithfulness=True))
    out.extend(metric_keys_for_block("planner", with_faithfulness=False))
    return tuple(out)


EXPECTED_TOP_LEVEL = (
    "keywords",
    "market",
    "competitor",
    "voc",
    "trends",
    "strategy",
)


def _is_list(value: Any) -> bool:
    return isinstance(value, list)


def _is_dict(value: Any) -> bool:
    return isinstance(value, dict)


def _metric_filled(value: Any) -> bool:
    if not _is_dict(value):
        return False
    raw_val = value.get("value")
    if raw_val not in (None, "", 0):
        return True
    desc = str(value.get("description") or "").strip()
    return bool(desc)


def _list_filled(value: Any) -> bool:
    return _is_list(value) and len(value) > 0


def _list_min_filled(value: Any, min_len: int = 2) -> bool:
    return _is_list(value) and len(value) >= min_len


def _sources_filled(value: Any) -> bool:
    if not _is_list(value):
        return False
    for item in value:
        if isinstance(item, dict):
            if (item.get("url") or item.get("domain") or item.get("source")):
                return True
        elif isinstance(item, str) and item.strip():
            return True
    return False


def _sources_min_filled(value: Any, min_count: int = 2) -> bool:
    if not _is_list(value):
        return False
    count = 0
    for item in value:
        if isinstance(item, dict):
            raw = (item.get("url") or item.get("domain") or item.get("source") or "")
            if str(raw).strip().startswith("http"):
                count += 1
        elif isinstance(item, str) and item.strip().startswith("http"):
            count += 1
    return count >= min_count


def _metric_filled_with_source(value: Any) -> bool:
    if not _metric_filled(value):
        return False
    src = str(value.get("source") or "").strip()
    return src.startswith("http")


def _voc_insights_filled(value: Any) -> bool:
    """Au moins 1 insight avec evidence_snippet vérifiable."""
    if not _is_list(value):
        return False
    for item in value:
        if not isinstance(item, dict):
            continue
        snippet = str(item.get("evidence_snippet") or "").strip()
        insight = str(item.get("insight") or "").strip()
        if len(snippet) >= 10 and len(insight) >= 5:
            return True
    return False


def _competitors_filled(value: Any) -> bool:
    """≥2 concurrents avec name + evidence_snippet."""
    if not _is_list(value):
        return False
    count = 0
    for comp in value:
        if not isinstance(comp, dict):
            continue
        name = str(comp.get("name") or "").strip()
        snippet = str(comp.get("evidence_snippet") or "").strip()
        if len(name) >= 2 and len(snippet) >= 10:
            count += 1
    return count >= 2


def _pestel_filled(value: Any) -> bool:
    if not _is_dict(value):
        return False
    axes = ("politique", "economique", "social", "technologique", "environnemental", "legal")
    filled_axes = sum(1 for axis in axes if _list_filled(value.get(axis)))
    return filled_axes >= 4


def _swot_filled(value: Any) -> bool:
    if not _is_dict(value):
        return False
    keys = ("forces", "faiblesses", "opportunites", "menaces")
    return all(_list_filled(value.get(k)) for k in keys)


def _demand_filled(value: Any) -> bool:
    if not _is_dict(value):
        return False
    level = str(value.get("demand_level") or "").strip()
    justification = str(value.get("demand_justification") or "").strip()
    return bool(level and justification)


def _strategic_filled(value: Any) -> bool:
    if not _is_dict(value):
        return False
    keys = (
        "main_opportunity",
        "main_risk",
        "recommendation",
        "segment_prioritaire",
        "message_cle_suggere",
    )
    filled = sum(1 for k in keys if str(value.get(k) or "").strip())
    return filled >= 4


def _keyword_lists_ok(block: str, field: str, value: Any) -> bool:
    return _is_list(value)


def _planner_section_ok(field: str, value: Any) -> bool:
    if not _is_dict(value):
        return False
    if field == "positioning":
        return bool(str(value.get("value_proposition") or value.get("target_segment") or "").strip())
    if field == "messaging":
        return bool(str(value.get("main_message") or "").strip())
    if field == "channels":
        return any(_is_dict(value.get(ch)) for ch in ("facebook", "instagram", "linkedin"))
    if field == "go_to_market":
        return bool(str(value.get("launch_strategy") or value.get("target_first_users") or "").strip())
    if field == "action_plan":
        st = value.get("short_term")
        return _is_dict(st) and _list_filled(st.get("actions"))
    return bool(value)


def _field_type_ok(block: str, field: str, value: Any) -> bool:
    if value is None:
        return False
    if block == "keywords":
        return _keyword_lists_ok(block, field, value)
    if block == "planner":
        if field in {"positioning", "messaging", "channels", "content_strategy", "budget_allocation", "go_to_market", "action_plan"}:
            return _is_dict(value)
        return True
    if block == "market" and field in {
        "market_size",
        "CAGR",
        "market_revenue",
        "growth_rate",
        "number_of_users",
        "adoption_rate",
    }:
        return _is_dict(value)
    if block == "market" and field == "market_signals":
        return _is_list(value)
    if block == "market" and field == "sources":
        return _is_list(value)
    if block == "voc" and field in {
        "pain_points",
        "frustrations",
        "desired_features",
        "market_insights",
        "user_quotes",
    }:
        return _is_list(value)
    if block == "voc" and field == "sources":
        return _is_list(value)
    if block == "competitor" and field == "competitors":
        return _is_list(value)
    if block == "trends" and field in {
        "market_trends",
        "consumer_trends",
        "technology_trends",
        "regulatory_trends",
        "opportunities",
        "risks",
    }:
        return _is_list(value)
    if block == "trends" and field == "sources":
        return _is_list(value)
    if block == "strategy" and field == "pestel":
        return _is_dict(value)
    if block == "strategy" and field == "swot":
        return _is_dict(value)
    if block == "strategy" and field == "demand_analysis":
        return _is_dict(value)
    if block == "strategy" and field == "strategic_insight":
        return _is_dict(value)
    return True


def _section_filled(block: str, field: str, value: Any) -> bool:
    if block == "keywords":
        return _list_min_filled(value, min_len=2)
    if block == "planner":
        return _planner_section_ok(field, value)
    if block == "market" and field in {"market_size", "CAGR"}:
        return _metric_filled_with_source(value)
    if block == "market" and field == "market_signals":
        return _list_min_filled(value, min_len=2)
    if block == "market" and field == "sources":
        return _sources_min_filled(value, min_count=2)
    if block == "voc" and field in {
        "pain_points",
        "frustrations",
        "desired_features",
        "market_insights",
    }:
        return _voc_insights_filled(value)
    if block == "voc" and field == "sources":
        return _sources_min_filled(value, min_count=1)
    if block == "competitor" and field == "competitors":
        return _competitors_filled(value)
    if block == "trends" and field in {"market_trends", "risks", "opportunities"}:
        return _list_min_filled(value, min_len=2)
    if block == "trends" and field == "sources":
        return _sources_min_filled(value, min_count=2)
    if block == "strategy" and field == "pestel":
        return _pestel_filled(value)
    if block == "strategy" and field == "swot":
        return _swot_filled(value)
    if block == "strategy" and field == "demand_analysis":
        return _demand_filled(value)
    if block == "strategy" and field == "strategic_insight":
        return _strategic_filled(value)
    return bool(value)


def block_format_compliance(block: str, data: dict) -> tuple[float, str]:
    fields = FORMAT_FIELDS.get(block, [])
    if not fields:
        return 1.0, "no schema"
    if not isinstance(data, dict) or not data:
        return 0.0, f"{block}: bloc vide ou absent"
    missing = []
    bad_type = []
    for field in fields:
        if field not in data:
            missing.append(field)
            continue
        if not _field_type_ok(block, field, data.get(field)):
            bad_type.append(field)
    if missing or bad_type:
        parts = []
        if missing:
            parts.append(f"manquants={missing}")
        if bad_type:
            parts.append(f"type_invalide={bad_type}")
        return 0.0, f"{block}: " + "; ".join(parts)
    return 1.0, f"{block}: ok"


def block_section_completeness(block: str, data: dict) -> tuple[float, str]:
    sections = SECTION_FIELDS.get(block, [])
    if not sections:
        return 1.0, "no sections"
    if not isinstance(data, dict) or not data:
        return 0.0, f"{block}: bloc vide"
    filled = 0
    empty = []
    for field in sections:
        if _section_filled(block, field, data.get(field)):
            filled += 1
        else:
            empty.append(field)
    score = filled / len(sections) if sections else 1.0
    return score, f"{block}: {filled}/{len(sections)} ({', '.join(empty) or 'ok'})"


def graph_format_compliance(market_analysis: dict) -> tuple[float, str]:
    if not isinstance(market_analysis, dict):
        return 0.0, "market_analysis invalide"
    missing_top = [k for k in EXPECTED_TOP_LEVEL if k not in market_analysis]
    if missing_top:
        return 0.0, f"cles_top_manquantes={missing_top}"
    comments = []
    scores = []
    for block in EVAL_BLOCKS:
        s, c = block_format_compliance(block, market_analysis.get(block) or {})
        scores.append(s)
        comments.append(c)
    ok = all(s == 1.0 for s in scores)
    return (1.0 if ok else 0.0), " | ".join(comments)


def graph_section_completeness(market_analysis: dict) -> tuple[float, str]:
    if not isinstance(market_analysis, dict):
        return 0.0, "market_analysis invalide"
    scores = []
    comments = []
    for block in EVAL_BLOCKS:
        s, c = block_section_completeness(block, market_analysis.get(block) or {})
        scores.append(s)
        comments.append(c)
    avg = sum(scores) / len(scores) if scores else 0.0
    return avg, " | ".join(comments)


def block_collected_sources(block: str, market_analysis: dict, *, max_chars: int = 8_000) -> str:
    """Sources / contexte pour faithfulness d'un bloc agent."""
    if not isinstance(market_analysis, dict):
        return "(aucune source)"
    if block == "strategy":
        parts = []
        for upstream in ("market", "voc", "trends", "competitor"):
            snippet = json.dumps(
                market_analysis.get(upstream) or {},
                ensure_ascii=False,
            )[:2000]
            parts.append(f"=== Intelligence amont ({upstream}) ===\n{snippet}")
        text = "\n\n".join(parts)
        return text[:max_chars] if len(text) > max_chars else text

    data = market_analysis.get(block) or {}
    if block == "competitor":
        lines = []
        for c in (data.get("competitors") or [])[:12]:
            if isinstance(c, dict):
                lines.append(
                    f"- {c.get('name')} | site={c.get('website')} | "
                    f"desc={str(c.get('description') or '')[:200]}"
                )
        return "\n".join(lines) or "(aucun concurrent extrait)"

    partial = {block: data}
    return aggregate_collected_sources(partial, max_chars=max_chars)


def aggregate_collected_sources(market_analysis: dict, *, max_chars: int = 24_000) -> str:
    """Construit le contexte sources pour faithfulness (URLs + extraits disponibles dans la sortie)."""
    if not isinstance(market_analysis, dict):
        return "(aucune source)"
    lines: list[str] = []

    def add_block(title: str, block: dict) -> None:
        if not isinstance(block, dict):
            return
        sources = block.get("sources")
        if isinstance(sources, list) and sources:
            lines.append(f"=== {title} — sources déclarées ===")
            for src in sources[:12]:
                if isinstance(src, dict):
                    lines.append(json_dumps_safe(src))
                else:
                    lines.append(str(src))
        if title == "market":
            for key in ("market_size", "CAGR", "growth_rate", "market_revenue"):
                metric = block.get(key)
                if isinstance(metric, dict) and metric.get("value") not in (None, ""):
                    lines.append(
                        f"[market.{key}] value={metric.get('value')} "
                        f"unit={metric.get('unit')} source={metric.get('source')}"
                    )
            for sig in (block.get("market_signals") or [])[:8]:
                if isinstance(sig, dict):
                    lines.append(
                        f"[signal] {sig.get('metric')}={sig.get('value')} "
                        f"source={sig.get('source')}"
                    )

    def json_dumps_safe(obj: Any) -> str:
        return json.dumps(obj, ensure_ascii=False)

    for key, label in (
        ("market", "MARKET"),
        ("voc", "VOC"),
        ("trends", "TRENDS"),
    ):
        add_block(label, market_analysis.get(key) or {})

    comp = market_analysis.get("competitor") or {}
    if isinstance(comp, dict):
        competitors = comp.get("competitors") or []
        if competitors:
            lines.append("=== COMPETITOR — sites extraits ===")
            for c in competitors[:10]:
                if isinstance(c, dict):
                    lines.append(
                        f"- {c.get('name')} | website={c.get('website')} | "
                        f"type={c.get('type')} | scope={c.get('scope')}"
                    )

    text = "\n".join(lines).strip()
    if not text:
        return "(aucune source structurée dans la sortie)"
    if len(text) > max_chars:
        return text[:max_chars] + "\n...[tronqué pour le judge]"
    return text
