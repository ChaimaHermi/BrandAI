from __future__ import annotations

import re
from typing import Any

from config.website_builder_config import REQUIRED_ANIMATIONS_MIN, REQUIRED_SECTIONS_MIN
from tools.website_builder.website_renderer import html_stats, validate_html_document


def validate_description_payload(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise RuntimeError("Description invalide : payload non dict.")

    sections = data.get("sections")
    if not isinstance(sections, list) or len(sections) < REQUIRED_SECTIONS_MIN:
        raise RuntimeError(
            f"Description invalide : il faut au moins {REQUIRED_SECTIONS_MIN} sections "
            f"(recu: {len(sections) if isinstance(sections, list) else 0})."
        )
    for idx, section in enumerate(sections):
        if not isinstance(section, dict):
            raise RuntimeError(f"Description invalide : section #{idx} n'est pas un objet.")
        if not str(section.get("title") or "").strip():
            raise RuntimeError(f"Description invalide : section #{idx} sans titre.")

    animations = data.get("animations")
    if not isinstance(animations, list) or len(animations) < REQUIRED_ANIMATIONS_MIN:
        raise RuntimeError(
            f"Description invalide : il faut au moins {REQUIRED_ANIMATIONS_MIN} animations "
            f"(recu: {len(animations) if isinstance(animations, list) else 0})."
        )

    for required_key in ("hero_concept", "user_summary", "tone_of_voice"):
        if not str(data.get(required_key) or "").strip():
            raise RuntimeError(f"Description invalide : champ '{required_key}' manquant.")


def validate_html_output(html: str) -> dict[str, int]:
    validate_html_document(html)
    _validate_navigation_integrity(html)
    _validate_image_integrity(html)
    _validate_responsive_integrity(html)
    return html_stats(html)


def validate_brand_identity(html: str, *, brand_name: str, slogan: str | None = None) -> None:
    lower = html.lower()
    brand = (brand_name or "").strip()
    slog = (slogan or "").strip()

    if brand and brand.lower() not in lower:
        raise RuntimeError(
            "Identite invalide : le nom de marque du contexte est absent du HTML genere."
        )
    if slog and slog.lower() not in lower:
        raise RuntimeError(
            "Identite invalide : le slogan du contexte n'est pas present tel quel dans le HTML genere."
        )


def sanitize_navigation_html(html: str) -> str:
    """
    Corrige automatiquement les ancres internes invalides les plus courantes:
    - href="#"
    - href="#missing-id"
    - href="/..." (liens app internes non permis)
    - href="javascript:..."
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
        lower_target = raw_target.lower()

        if raw_target.startswith(("http://", "https://", "mailto:", "tel:")):
            return match.group(0)

        if (
            raw_target == "#"
            or raw_target.startswith("/")
            or lower_target.startswith("javascript:")
            or raw_target == ""
        ):
            return f'href={quote}#{fallback_id}{quote}'

        if raw_target.startswith("#"):
            anchor = raw_target[1:]
            if not anchor:
                return f'href={quote}#{fallback_id}{quote}'
            return match.group(0)

        return f'href={quote}#{fallback_id}{quote}'

    sanitized = re.sub(r'href\s*=\s*(["\'])([^"\']*)\1', _replace, html, flags=re.IGNORECASE)

    # Si des ancres internes existent sans id correspondant (ex: #cgu, #presse),
    # on ajoute des cibles minimales avant </body> pour garder une navigation
    # fonctionnelle au lieu de casser le menu.
    all_ids = set(re.findall(r'id\s*=\s*["\']([^"\']+)["\']', sanitized, flags=re.IGNORECASE))
    hrefs = _HREF_RE.findall(sanitized)
    internal_anchors = [
        h[1:].strip()
        for h in hrefs
        if h.startswith("#") and len(h) > 1
    ]
    missing_ids = []
    for anchor in internal_anchors:
        slug = re.sub(r"[^a-z0-9_-]+", "-", anchor.lower()).strip("-")
        if not slug:
            continue
        if slug not in all_ids and slug not in missing_ids:
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


_HREF_RE = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_ATTR_RE = re.compile(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*["\']([^"\']*)["\']')
_WINDOW_NAV_RE = re.compile(
    r"(window\.location\s*=|location\.href\s*=|location\.assign\s*\(|location\.replace\s*\()",
    re.IGNORECASE,
)
_PLACEHOLDER_IMG_HOST_RE = re.compile(
    r"(via\.placeholder\.com|placehold\.co|placeholder\.com|dummyimage\.com)",
    re.IGNORECASE,
)


def _is_external_href(href: str) -> bool:
    return href.startswith(("http://", "https://", "mailto:", "tel:"))


def _validate_navigation_integrity(html: str) -> None:
    lower = html.lower()
    if _WINDOW_NAV_RE.search(lower):
        raise RuntimeError(
            "Navigation invalide : script de redirection detecte (window.location/location.href). "
            "Utiliser uniquement des ancres internes #id pour nav/CTA."
        )

    hrefs = _HREF_RE.findall(html)
    internal_targets = [h.strip() for h in hrefs if h and not _is_external_href(h.strip())]
    bad_targets = [
        h for h in internal_targets
        if (h == "#" or h.startswith("/") or h.lower().startswith("javascript:"))
    ]
    if bad_targets:
        sample = ", ".join(bad_targets[:5])
        raise RuntimeError(
            "Navigation invalide : liens internes non permis detectes "
            f"({sample}). Utiliser des ancres #section-id."
        )

    # Vérifie que toutes les ancres #id pointent vers des ids existants.
    anchor_targets = [h[1:] for h in internal_targets if h.startswith("#") and len(h) > 1]
    ids = set(re.findall(r'id\s*=\s*["\']([^"\']+)["\']', html, flags=re.IGNORECASE))
    missing = [t for t in anchor_targets if t not in ids]
    if missing:
        sample = ", ".join(missing[:5])
        raise RuntimeError(
            "Navigation invalide : ancres sans section cible detectees "
            f"({sample})."
        )


def _validate_image_integrity(html: str) -> None:
    lower = html.lower()
    if "image indisponible" in lower:
        raise RuntimeError(
            "Image invalide : le HTML contient le texte interdit 'Image indisponible'. "
            "Supprimer l'image incertaine au lieu d'afficher ce fallback."
        )

    img_tags = _IMG_TAG_RE.findall(html)
    for idx, tag in enumerate(img_tags, start=1):
        attrs = {k.lower(): v for k, v in _ATTR_RE.findall(tag)}
        src = (attrs.get("src") or "").strip()
        alt = (attrs.get("alt") or "").strip()
        if not src:
            raise RuntimeError(f"Image invalide : balise <img> #{idx} sans src.")
        if not (src.startswith(("http://", "https://", "data:"))):
            raise RuntimeError(
                f"Image invalide : src non autorise sur <img> #{idx} ({src!r}). "
                "Utiliser http(s) ou data URI."
            )
        if _PLACEHOLDER_IMG_HOST_RE.search(src):
            raise RuntimeError(
                f"Image invalide : src placeholder non autorise sur <img> #{idx} ({src!r})."
            )
        if not alt:
            raise RuntimeError(f"Image invalide : balise <img> #{idx} sans alt.")


def _validate_responsive_integrity(html: str) -> None:
    lower = html.lower()
    if '<meta name="viewport"' not in lower:
        raise RuntimeError(
            "Responsive invalide : meta viewport manquante."
        )

    # Heuristique: un site vitrine responsive doit utiliser plusieurs breakpoints.
    responsive_tokens = ("sm:", "md:", "lg:", "xl:", "2xl:")
    responsive_hits = sum(lower.count(token) for token in responsive_tokens)
    if responsive_hits < 4:
        raise RuntimeError(
            "Responsive invalide : trop peu de classes responsive detectees "
            "(attendu: au moins 4 occurrences de sm:/md:/lg:/xl:)."
        )

    # Au moins un menu mobile/burger ou un pattern de nav adaptatif.
    nav_mobile_markers = ("mobile", "burger", "menu-toggle", "md:hidden", "hidden md:")
    if not any(marker in lower for marker in nav_mobile_markers):
        raise RuntimeError(
            "Responsive invalide : aucun marqueur de navigation mobile detecte."
        )

