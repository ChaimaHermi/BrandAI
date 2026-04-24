"""Branding normalizers shared by branding agents."""

from __future__ import annotations

import re
from typing import Any

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def normalize_slogan_options(raw: list) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if isinstance(item, str) and item.strip():
            out.append({"text": item.strip(), "rationale": ""})
            continue
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or item.get("slogan") or "").strip()
        if not text:
            continue
        rationale = str(item.get("rationale") or item.get("description") or "").strip()
        out.append({"text": text, "rationale": rationale})
    return out


def _normalize_hex(h: str) -> str | None:
    t = (h or "").strip()
    if not t:
        return None
    if t.startswith("#") and len(t) == 7 and _HEX_RE.match(t):
        return t.upper()
    if len(t) == 6 and re.match(r"^[0-9A-Fa-f]{6}$", t):
        return "#" + t.upper()
    return None


def _normalize_swatches(raw: list) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("label") or "").strip()
        hx = _normalize_hex(str(item.get("hex") or item.get("color") or ""))
        if not name or not hx:
            continue
        role = str(item.get("role") or "accent").strip() or "accent"
        rationale = str(item.get("rationale") or item.get("description") or "").strip()
        out.append({"name": name, "hex": hx, "role": role, "rationale": rationale})
    return out


def normalize_palette_options(raw: list) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        pname = str(item.get("palette_name") or item.get("name") or "").strip()
        desc = str(item.get("palette_description") or item.get("why_palette") or "").strip()
        sw = _normalize_swatches(item.get("swatches") or item.get("colors") or [])
        if not pname or len(sw) < 2:
            continue
        out.append({
            "palette_name": pname,
            "palette_description": desc,
            "swatches": sw,
        })
    return out
