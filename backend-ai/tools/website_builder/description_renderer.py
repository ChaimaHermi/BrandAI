"""
Helpers de présentation pour le chat (Phase 1 + Phase 2).

Convertit les structures Python en Markdown lisible directement par
le frontend dans une bulle de message.
"""

from __future__ import annotations

from typing import Any

from tools.website_builder.brand_context_fetch import BrandContext


def render_context_summary(ctx: BrandContext) -> str:
    """Résumé Phase 1 affiché au user au démarrage du chat."""
    lines = [
        "J'ai récupéré ton projet :",
        "",
        f"**Nom** : {ctx.project_name}",
        f"**Marque** : {ctx.brand_name}"
        + (f' — *« {ctx.slogan} »*' if ctx.slogan else ""),
        f"**Secteur** : {ctx.sector or '—'}",
        f"**Cible** : {ctx.target_audience or '—'}",
        "",
        f"**Couleurs** : `{ctx.primary_color}` · `{ctx.secondary_color}` · `{ctx.accent_color}`",
        f"**Fond** : `{ctx.background_color}`",
        f"**Fonts** : {ctx.title_font} · {ctx.body_font}",
        f"**Palette** : {ctx.palette_direction}",
    ]
    if ctx.logo_url:
        lines.append(f"**Logo** : {ctx.logo_url}")

    brief = ctx.short_pitch or ctx.description_brief
    if brief:
        snippet = brief if len(brief) <= 280 else brief[:277] + "…"
        lines.extend(["", f"**Brief** : {snippet}"])

    return "\n".join(lines)


def render_description_summary(data: dict[str, Any]) -> str:
    """Résumé Phase 2 — montre au user ce que l'agent va construire."""
    lines: list[str] = []

    user_summary = str(data.get("user_summary") or "").strip()
    if user_summary:
        lines.append(user_summary)
        lines.append("")

    hero = str(data.get("hero_concept") or "").strip()
    if hero:
        lines.append(f"**Concept hero** : {hero}")

    style = str(data.get("visual_style") or "").strip()
    if style:
        lines.append(f"**Direction visuelle** : {style}")

    tone = str(data.get("tone_of_voice") or "").strip()
    if tone:
        lines.append(f"**Ton éditorial** : {tone}")

    pairing = str(data.get("typography_pairing") or "").strip()
    if pairing:
        lines.append(f"**Typographie** : {pairing}")

    color_usage = data.get("color_usage")
    if isinstance(color_usage, dict) and color_usage:
        # Compat: supporte l'ancien format (primary/secondary/...) et le nouveau
        # format créatif (dominant/supporting/highlight/...).
        keys_priority = [
            "dominant",
            "supporting",
            "highlight",
            "surfaces",
            "gradients_fx",
            "primary",
            "secondary",
            "accent",
            "surface",
            "background",
        ]
        color_lines: list[str] = []
        for key in keys_priority:
            value = str(color_usage.get(key) or "").strip()
            if value:
                pretty_key = key.replace("_", " ")
                color_lines.append(f"- **{pretty_key}** : {value}")
        if color_lines:
            lines.append("")
            lines.append("**Stratégie couleur** :")
            lines.extend(color_lines)

    sections = data.get("sections") or []
    if isinstance(sections, list) and sections:
        lines.append("")
        lines.append("**Sections prévues** :")
        for s in sections:
            if not isinstance(s, dict):
                continue
            title = str(s.get("title") or s.get("id") or "").strip()
            touch = str(s.get("creative_touch") or "").strip()
            bullet = f"- **{title}**"
            if touch:
                bullet += f" — {touch}"
            lines.append(bullet)

    animations = data.get("animations") or []
    if isinstance(animations, list) and animations:
        lines.append("")
        lines.append("**Animations** :")
        for anim in animations:
            text = str(anim).strip()
            if text:
                lines.append(f"- {text}")

    lines.extend([
        "",
        "**Approuver** pour générer le site, ou **Modifier** pour ajuster cette description.",
    ])
    return "\n".join(lines)
