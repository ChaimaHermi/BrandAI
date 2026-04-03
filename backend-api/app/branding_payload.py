"""Découpage / fusion du payload Brand Identity (colonnes structurées + méta JSON)."""

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
    """
    Extrait méta (reste), noms, slogans, logo à partir d’un dict « monolithique ».
    """
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


def merge_brand_identity_for_api(
    *,
    result_json: dict[str, Any] | None,
    result_names: dict[str, Any] | None,
    result_slogans: dict[str, Any] | None,
    result_logo: dict[str, Any] | None,
) -> dict[str, Any]:
    """Vue fusionnée pour les clients (ex. même forme qu’avant un seul result_json)."""
    merged: dict[str, Any] = {}
    if result_json:
        merged.update(result_json)
    for block in (result_names, result_slogans, result_logo):
        if isinstance(block, dict) and block:
            merged.update(block)
    return merged
