from __future__ import annotations

import re
from typing import Any


_HREF_RE = re.compile(r'href\s*=\s*(["\'])([^"\']*)\1', re.IGNORECASE)
_ALL_HREFS_RE = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)


def sanitize_navigation_html(html: str) -> str:
    """
    Corrige automatiquement les ancres internes invalides :
    - href="#" vide
    - href="/..." (liens app internes)
    - href="javascript:..."
    - Ajoute des cibles minimales pour les ancres sans id correspondant.
    Ne lève jamais d'exception — nettoyage silencieux.
    """
    if not html or "href" not in html.lower():
        return html

    ids = re.findall(r'id\s*=\s*["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
    fallback_id = "hero" if "hero" in ids else (ids[0] if ids else None)
    if not fallback_id:
        return html

    id_set = set(ids)

    def _replace(match: re.Match[str]) -> str:
        quote = match.group(1)
        raw_target = (match.group(2) or "").strip()

        if raw_target.startswith(("http://", "https://", "mailto:", "tel:")):
            return match.group(0)
        if (
            raw_target == "#"
            or raw_target.startswith("/")
            or raw_target.lower().startswith("javascript:")
            or raw_target == ""
        ):
            return f'href={quote}#{fallback_id}{quote}'
        if raw_target.startswith("#"):
            return match.group(0)
        return f'href={quote}#{fallback_id}{quote}'

    sanitized = _HREF_RE.sub(_replace, html)

    # Ajoute des sections cibles vides pour les ancres sans id correspondant.
    all_ids = set(re.findall(r'id\s*=\s*["\']([^"\']+)["\']', sanitized, flags=re.IGNORECASE))
    hrefs = _ALL_HREFS_RE.findall(sanitized)
    missing_ids = []
    for h in hrefs:
        if not h.startswith("#") or len(h) <= 1:
            continue
        slug = re.sub(r"[^a-z0-9_-]+", "-", h[1:].lower()).strip("-")
        if slug and slug not in all_ids and slug not in missing_ids:
            missing_ids.append(slug)

    if missing_ids:
        stubs = "".join(
            f'\n<section id="{sid}" style="scroll-margin-top:80px;min-height:1px;" aria-hidden="true"></section>'
            for sid in missing_ids
        )
        if "</body>" in sanitized.lower():
            sanitized = re.sub(r"</body>", f"{stubs}\n</body>", sanitized, flags=re.IGNORECASE)
        else:
            sanitized = f"{sanitized}{stubs}"

    return sanitized


def validate_description_payload(data: dict[str, Any]) -> None:
    """Validation minimale de la description Phase 2 : dict non-vide avec des sections."""
    if not isinstance(data, dict) or not data:
        raise RuntimeError("Description invalide : payload vide ou non-dict.")
    sections = data.get("sections")
    if not isinstance(sections, list) or len(sections) == 0:
        raise RuntimeError("Description invalide : 'sections' manquant ou vide.")
