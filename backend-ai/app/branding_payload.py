"""Aligné sur backend-api/app/branding_payload.py — découpage pour persistance structurée."""

from __future__ import annotations

from typing import Any

NAME_KEYS = frozenset({"name_options", "name_error"})
SLOGAN_KEYS = frozenset({"slogan_options", "chosen_brand_name", "slogan_error"})
LOGO_KEYS = frozenset({
    "logo_concepts",
    "color_palette",
    "palette_options",
    "palette_error",
})


def split_brand_identity_payload(full: dict[str, Any] | None) -> tuple[
    dict[str, Any] | None,
    dict[str, Any] | None,
    dict[str, Any] | None,
    dict[str, Any] | None,
]:
    if not full:
        return None, None, None, None
    d = dict(full)
    names = {k: d.pop(k) for k in list(d.keys()) if k in NAME_KEYS}
    slogans = {k: d.pop(k) for k in list(d.keys()) if k in SLOGAN_KEYS}
    logo = {k: d.pop(k) for k in list(d.keys()) if k in LOGO_KEYS}
    meta = d if d else None
    return (
        meta,
        names if names else None,
        slogans if slogans else None,
        logo if logo else None,
    )
