"""Branding validators shared by branding agents."""

from __future__ import annotations

import json
import re
from typing import Any

from shared.branding.normalizers import normalize_palette_options, normalize_slogan_options


def parse_llm_json_object(raw: str) -> dict:
    """Parse model output; tolerates markdown fences and surrounding prose."""
    if raw is None:
        raise json.JSONDecodeError("Invalid JSON (empty response)", "", 0)

    s = str(raw).strip()
    if not s:
        raise json.JSONDecodeError("Invalid JSON (empty response)", raw or "", 0)

    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", s, flags=re.IGNORECASE).strip()

    try:
        out = json.loads(cleaned)
        if isinstance(out, dict):
            return out
    except json.JSONDecodeError:
        pass

    brace_start = cleaned.find("{")
    if brace_start >= 0:
        depth = 0
        for i, ch in enumerate(cleaned[brace_start:], start=brace_start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        out = json.loads(cleaned[brace_start : i + 1])
                        if isinstance(out, dict):
                            return out
                    except json.JSONDecodeError:
                        break

    preview = (s[:120] + "...") if len(s) > 120 else s
    raise json.JSONDecodeError(f"Invalid JSON (no parseable object): {preview!r}", s, 0)


def _normalize_text(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def validate_minimal_slogans(raw: str, *, target: int) -> list[dict[str, Any]]:
    data = parse_llm_json_object(raw)
    raw_opts = data.get("slogan_options")
    if not isinstance(raw_opts, list):
        raise ValueError("Cle slogan_options manquante ou invalide.")

    options = normalize_slogan_options(raw_opts)
    if len(options) < target:
        raise ValueError(f"Attendu au moins {target} slogans exploitables, recu {len(options)}.")

    selected = options[:target]
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for i, item in enumerate(selected):
        text = str(item.get("text") or "").strip()
        if not text:
            raise ValueError(f"Slogan {i + 1}: champ text vide.")
        sig = _normalize_text(text)
        if sig in seen:
            raise ValueError("Slogans en doublon detectes.")
        seen.add(sig)
        out.append({
            "text": text,
            "rationale": str(item.get("rationale") or "").strip(),
        })
    return out


def _palette_signature(option: dict[str, Any]) -> frozenset[str]:
    swatches = option.get("swatches") or []
    hexes: list[str] = []
    for sw in swatches:
        if isinstance(sw, dict):
            hx = str(sw.get("hex") or "").strip().upper()
            if hx:
                hexes.append(hx)
    return frozenset(hexes)


def validate_minimal_palettes(raw: str, *, target: int) -> list[dict[str, Any]]:
    data = parse_llm_json_object(raw)
    raw_opts = data.get("palette_options")
    if raw_opts is None and isinstance(data.get("palettes"), list):
        raw_opts = data.get("palettes")
    if not isinstance(raw_opts, list):
        raise ValueError("Cle palette_options manquante ou invalide.")

    options = normalize_palette_options(raw_opts)
    if len(options) < target:
        raise ValueError(f"Attendu au moins {target} palettes exploitables, recu {len(options)}.")

    selected = options[:target]
    signatures: set[frozenset[str]] = set()
    for i, option in enumerate(selected):
        swatches = option.get("swatches") or []
        if len(swatches) < 3:
            raise ValueError(f"Palette {i + 1}: au moins 3 couleurs requises.")
        sig = _palette_signature(option)
        if sig in signatures:
            raise ValueError("Palettes en doublon detectees.")
        signatures.add(sig)
    return selected
