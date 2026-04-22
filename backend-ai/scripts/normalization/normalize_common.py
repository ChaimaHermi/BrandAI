from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
RAW_DIR = RESULTS_DIR / "raw"
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


def parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def safe_int(value: Any) -> int:
    if isinstance(value, bool) or value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(str(value).strip())
    except Exception:
        return 0


def first_phrase(value: Any, max_len: int = 140) -> str | None:
    if not isinstance(value, str):
        return None
    text = " ".join(value.strip().split())
    if not text:
        return None

    separators = [". ", "! ", "? ", "\n"]
    cut = len(text)
    for sep in separators:
        idx = text.find(sep)
        if idx != -1:
            cut = min(cut, idx + 1)
    phrase = text[:cut].strip()
    if len(phrase) > max_len:
        return phrase[: max_len - 1].rstrip() + "…"
    return phrase
