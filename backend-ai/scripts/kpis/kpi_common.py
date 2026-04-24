from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
NORMALIZED_DIR = RESULTS_DIR / "normalized"
KPI_DIR = RESULTS_DIR / "kpis"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"Invalid JSON object in {path}")
    return data


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def safe_div(num: float | int, den: float | int) -> float | None:
    if den in (0, None):
        return None
    try:
        return float(num) / float(den)
    except Exception:
        return None


def pct(num: float | int, den: float | int) -> float | None:
    base = safe_div(num, den)
    return round(base * 100.0, 4) if base is not None else None


def post_days_span(posts: list[dict[str, Any]]) -> int:
    dates = []
    for p in posts:
        value = p.get("published_at")
        if not isinstance(value, str) or not value.strip():
            continue
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            dates.append(dt.date())
        except Exception:
            continue
    if not dates:
        return 0
    return (max(dates) - min(dates)).days + 1
