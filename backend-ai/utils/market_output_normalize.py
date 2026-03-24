# ══════════════════════════════════════════════════════════════
#  Valeurs par défaut + complétion du JSON market_analysis
#  Aligné sur prompts/market_prompts.py (output_schema)
# ══════════════════════════════════════════════════════════════

from __future__ import annotations

import copy
from typing import Any


def _empty_competitor() -> dict:
    return {
        "name": "",
        "url": "",
        "type": "indirect",
        "strengths": [],
        "weaknesses": [],
        "threat_score": 0,
        "data_source": "",
    }


def _empty_trend() -> dict:
    return {
        "keyword": "",
        "direction": "STABLE",
        "signal_strength": "LOW",
        "insight": "",
        "data_source": "",
    }


def _empty_risk() -> dict:
    return {
        "category": "market",
        "description": "",
        "severity": "MEDIUM",
        "mitigation": "",
    }


def _empty_opportunity() -> dict:
    return {
        "title": "",
        "description": "",
        "time_horizon": "medium (6-18m)",
    }


def _empty_recommendation() -> dict:
    return {
        "title": "",
        "description": "",
        "priority": "MEDIUM",
        "rationale": "",
    }


def market_analysis_template() -> dict:
    """Schéma cible (structure + défauts) pour l'output market analysis."""
    return {
        "market_overview": {
            "sector": "",
            "tam_global_usd": "",
            "tam_cagr_pct": 0,
            "sam_local_usd": "",
            "sam_rationale": "",
            "market_maturity_score": 0,
            "market_maturity_label": "nascent",
            "timing_signal": "",
        },
        "competitors": [],
        "swot": {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
        },
        "trends": [],
        "voice_of_customer": {
            "top_pain_points": [],
            "desired_features": [],
            "competitor_frustrations": [],
            "youtube_voc_signals": [],
            "sources": [],
        },
        "risks": [],
        "opportunities": [],
        "kpis": {
            "addressable_students_local": 0,
            "internet_penetration_pct": 0,
            "mobile_penetration_per100": 0,
            "gdp_per_capita_usd": 0,
            "recommended_pricing_model": "",
            "estimated_cac_usd": "",
            "market_maturity_score": 0,
        },
        "recommendations": [],
        "data_quality": {
            "sources_used": [],
            "confidence_score": 0,
            "missing_data_notes": "",
        },
    }


def _ensure_list_of_dicts(items: Any, factory: dict) -> list:
    if not isinstance(items, list):
        return []
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        merged = copy.deepcopy(factory)
        merged.update({k: v for k, v in it.items() if k in factory})
        if "strengths" in factory and isinstance(it.get("strengths"), list):
            merged["strengths"] = [str(x) for x in it["strengths"]]
        if "weaknesses" in factory and isinstance(it.get("weaknesses"), list):
            merged["weaknesses"] = [str(x) for x in it["weaknesses"]]
        out.append(merged)
    return out


def _ensure_str_list(x: Any) -> list:
    if not isinstance(x, list):
        return []
    return [str(i) for i in x if i is not None]


def normalize_market_analysis(data: Any) -> dict:
    """
    Complète le dict renvoyé par le LLM avec toutes les clés attendues.
    Ne supprime pas les champs extra validement produits par le modèle.
    """
    if not isinstance(data, dict):
        data = {}

    tmpl = market_analysis_template()
    out: dict[str, Any] = {}

    # Top-level keys manquants -> template
    for key in tmpl:
        if key not in data:
            out[key] = copy.deepcopy(tmpl[key])
        else:
            out[key] = data[key]

    # market_overview
    mo_t = tmpl["market_overview"]
    mo = out["market_overview"]
    if not isinstance(mo, dict):
        mo = {}
    for k, default in mo_t.items():
        if k not in mo or mo[k] is None:
            mo[k] = copy.deepcopy(default)
    # types simples
    if not isinstance(mo.get("tam_cagr_pct"), (int, float)):
        try:
            mo["tam_cagr_pct"] = float(mo.get("tam_cagr_pct") or 0)
        except (TypeError, ValueError):
            mo["tam_cagr_pct"] = 0
    for fk in ("sector", "tam_global_usd", "sam_local_usd", "sam_rationale", "market_maturity_label", "timing_signal"):
        if mo.get(fk) is None:
            mo[fk] = ""
        elif fk not in ("tam_cagr_pct",) and not isinstance(mo[fk], str):
            mo[fk] = str(mo[fk])
    if not isinstance(mo.get("market_maturity_score"), (int, float)):
        try:
            mo["market_maturity_score"] = int(mo.get("market_maturity_score") or 0)
        except (TypeError, ValueError):
            mo["market_maturity_score"] = 0
    out["market_overview"] = mo

    # competitors
    comp = out.get("competitors")
    out["competitors"] = _ensure_list_of_dicts(comp, _empty_competitor())
    for c in out["competitors"]:
        try:
            c["threat_score"] = max(0, min(100, int(float(c.get("threat_score", 0)))))
        except (TypeError, ValueError):
            c["threat_score"] = 0

    # swot
    sw = out.get("swot")
    if not isinstance(sw, dict):
        sw = {}
    for k in tmpl["swot"]:
        if k not in sw:
            sw[k] = []
        else:
            sw[k] = _ensure_str_list(sw[k])
    out["swot"] = sw

    # trends
    out["trends"] = _ensure_list_of_dicts(out.get("trends"), _empty_trend())

    # voice_of_customer
    voc = out.get("voice_of_customer")
    if not isinstance(voc, dict):
        voc = {}
    for k in tmpl["voice_of_customer"]:
        if k not in voc:
            voc[k] = []
        else:
            voc[k] = _ensure_str_list(voc[k])
    out["voice_of_customer"] = voc

    out["risks"] = _ensure_list_of_dicts(out.get("risks"), _empty_risk())
    out["opportunities"] = _ensure_list_of_dicts(out.get("opportunities"), _empty_opportunity())

    # kpis
    kp = out.get("kpis")
    if not isinstance(kp, dict):
        kp = {}
    for k, default in tmpl["kpis"].items():
        if k not in kp or kp[k] is None:
            kp[k] = copy.deepcopy(default)
    for nk in (
        "addressable_students_local",
        "internet_penetration_pct",
        "mobile_penetration_per100",
        "gdp_per_capita_usd",
        "market_maturity_score",
    ):
        try:
            kp[nk] = int(float(kp.get(nk) or 0))
        except (TypeError, ValueError):
            kp[nk] = 0
    for sk in ("recommended_pricing_model", "estimated_cac_usd"):
        if kp.get(sk) is None:
            kp[sk] = ""
        elif not isinstance(kp[sk], str):
            kp[sk] = str(kp[sk])
    out["kpis"] = kp

    out["recommendations"] = _ensure_list_of_dicts(out.get("recommendations"), _empty_recommendation())

    # data_quality
    dq = out.get("data_quality")
    if not isinstance(dq, dict):
        dq = {}
    if "sources_used" not in dq or not isinstance(dq.get("sources_used"), list):
        dq["sources_used"] = []
    else:
        dq["sources_used"] = [str(s) for s in dq["sources_used"] if s is not None]
    if "confidence_score" not in dq or dq["confidence_score"] is None:
        dq["confidence_score"] = 0
    else:
        try:
            dq["confidence_score"] = max(0, min(100, int(float(dq["confidence_score"]))))
        except (TypeError, ValueError):
            dq["confidence_score"] = 0
    if "missing_data_notes" not in dq or dq["missing_data_notes"] is None:
        dq["missing_data_notes"] = ""
    elif not isinstance(dq["missing_data_notes"], str):
        dq["missing_data_notes"] = str(dq["missing_data_notes"])
    out["data_quality"] = dq

    # Réinjecter clés LLM additionnelles non listées dans le template
    for k, v in data.items():
        if k not in out:
            out[k] = v

    return out
