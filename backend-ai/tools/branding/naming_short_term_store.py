"""
Mémoire courte « exists names » (Brandfetch) : même format JSON qu’avant, stocké dans SQLite.

Un fichier `data/memory/naming_short_term.db` remplace les fichiers `idea_*_exists_names.json`.
Migration automatique à la première lecture si un JSON legacy existe encore.
"""

from __future__ import annotations

import json
import re
import sqlite3
import threading
from pathlib import Path

from config.branding_config import (
    NAME_EXISTS_MEMORY_MAX,
    NAME_SHORT_TERM_MEMORY_DIR,
    NAME_SHORT_TERM_SQLITE_PATH,
)

_lock = threading.Lock()


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").strip().lower())


def _backend_ai_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _db_path() -> Path:
    p = _backend_ai_root() / NAME_SHORT_TERM_SQLITE_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS naming_exists_memory (
            idea_id INTEGER PRIMARY KEY NOT NULL,
            payload TEXT NOT NULL
        )
        """
    )
    conn.commit()


def _legacy_json_path(idea_id: int) -> Path:
    return _backend_ai_root() / NAME_SHORT_TERM_MEMORY_DIR / f"idea_{idea_id}_exists_names.json"


def _normalize_list(names: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for n in names:
        norm = _normalize_name(str(n))
        if not norm or norm in seen:
            continue
        seen.add(norm)
        out.append(norm)
    return out[-NAME_EXISTS_MEMORY_MAX:]


def _load_payload_from_legacy_json(idea_id: int) -> dict | None:
    path = _legacy_json_path(idea_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        names = data.get("exists_names", [])
        if not isinstance(names, list):
            return None
        deduped = _normalize_list([str(x) for x in names])
        return {"idea_id": idea_id, "exists_names": deduped}
    except Exception:
        return None


def load_exists_memory(idea_id: int | str | None) -> list[str]:
    if idea_id in (None, ""):
        return []
    try:
        iid = int(idea_id)
    except (TypeError, ValueError):
        return []

    with _lock:
        conn = sqlite3.connect(str(_db_path()), check_same_thread=False)
        try:
            _ensure_schema(conn)
            row = conn.execute(
                "SELECT payload FROM naming_exists_memory WHERE idea_id = ?",
                (iid,),
            ).fetchone()
            if row is None:
                legacy = _load_payload_from_legacy_json(iid)
                if legacy is None:
                    return []
                payload = json.dumps(legacy, ensure_ascii=False)
                conn.execute(
                    """
                    INSERT INTO naming_exists_memory (idea_id, payload) VALUES (?, ?)
                    ON CONFLICT(idea_id) DO UPDATE SET payload = excluded.payload
                    """,
                    (iid, payload),
                )
                conn.commit()
                names = legacy.get("exists_names", [])
            else:
                try:
                    data = json.loads(row[0])
                    names = data.get("exists_names", []) if isinstance(data, dict) else []
                except Exception:
                    names = []
            if not isinstance(names, list):
                return []
            return _normalize_list([str(x) for x in names])
        finally:
            conn.close()


def save_exists_memory(idea_id: int | str | None, exists_names: list[str]) -> None:
    if idea_id in (None, ""):
        return
    try:
        iid = int(idea_id)
    except (TypeError, ValueError):
        return

    deduped = _normalize_list(exists_names)
    payload = json.dumps({"idea_id": iid, "exists_names": deduped}, ensure_ascii=False)

    with _lock:
        conn = sqlite3.connect(str(_db_path()), check_same_thread=False)
        try:
            _ensure_schema(conn)
            conn.execute(
                """
                INSERT INTO naming_exists_memory (idea_id, payload) VALUES (?, ?)
                ON CONFLICT(idea_id) DO UPDATE SET payload = excluded.payload
                """,
                (iid, payload),
            )
            conn.commit()
        finally:
            conn.close()


def append_exists_memory(idea_id: int | str | None, names: list[str]) -> None:
    if not names:
        return
    current = load_exists_memory(idea_id)
    merged = current + [str(n) for n in names]
    save_exists_memory(idea_id, merged)
