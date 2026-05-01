from __future__ import annotations

import re
from typing import Any

from config.website_builder_config import REQUIRED_ANIMATIONS_MIN, REQUIRED_SECTIONS_MIN
from tools.website_builder.website_renderer import html_stats, validate_html_document


def validate_architecture_payload(data: dict[str, Any]) -> None:
    """Valide la structure produite par architecture_tool (Phase 2A)."""
    if not isinstance(data, dict):
        raise RuntimeError("Architecture invalide : payload non dict.")

    sections = data.get("sections")
    if not isinstance(sections, list) or len(sections) < REQUIRED_SECTIONS_MIN:
        raise RuntimeError(
            f"Architecture invalide : il faut au moins {REQUIRED_SECTIONS_MIN} sections "
            f"(recu: {len(sections) if isinstance(sections, list) else 0})."
        )

    section_ids: list[str] = []
    section_types: list[str] = []
    for idx, section in enumerate(sections):
        if not isinstance(section, dict):
            raise RuntimeError(f"Architecture invalide : section #{idx} n'est pas un objet.")
        sid = str(section.get("id") or "").strip()
        stype = str(section.get("type") or "").strip()
        if not sid:
            raise RuntimeError(f"Architecture invalide : section #{idx} sans id.")
        if not stype:
            raise RuntimeError(f"Architecture invalide : section #{idx} sans type.")
        if sid in section_ids:
            raise RuntimeError(f"Architecture invalide : id de section dupliqué '{sid}'.")
        section_ids.append(sid)
        section_types.append(stype)

    if section_types[0] != "hero":
        raise RuntimeError("Architecture invalide : la première section doit être de type 'hero'.")
    if section_types[-1] != "footer":
        raise RuntimeError("Architecture invalide : la dernière section doit être de type 'footer'.")
    if "contact" not in section_types:
        raise RuntimeError("Architecture invalide : une section 'contact' est obligatoire.")

    nav_links = data.get("nav_links") or []
    if not isinstance(nav_links, list):
        raise RuntimeError("Architecture invalide : nav_links doit être une liste.")
    for idx, link in enumerate(nav_links):
        target = str((link or {}).get("target_id") or "").strip()
        if target and target not in section_ids:
            raise RuntimeError(
                f"Architecture invalide : nav_links[{idx}].target_id='{target}' "
                f"ne correspond à aucune section."
            )

    animations = data.get("animations")
    if not isinstance(animations, list) or len(animations) < REQUIRED_ANIMATIONS_MIN:
        raise RuntimeError(
            f"Architecture invalide : il faut au moins {REQUIRED_ANIMATIONS_MIN} animations "
            f"(recu: {len(animations) if isinstance(animations, list) else 0})."
        )


def validate_content_payload(data: dict[str, Any], architecture: dict[str, Any]) -> None:
    """Valide la cohérence du contenu avec l'architecture (Phase 2B)."""
    if not isinstance(data, dict):
        raise RuntimeError("Contenu invalide : payload non dict.")

    sections = data.get("sections")
    if not isinstance(sections, dict):
        raise RuntimeError("Contenu invalide : sections doit être un dict id→contenu.")

    arch_sections = architecture.get("sections") or []
    expected_ids = [
        str(s.get("id") or "").strip() for s in arch_sections if isinstance(s, dict)
    ]
    expected_ids = [sid for sid in expected_ids if sid]

    missing = [sid for sid in expected_ids if sid not in sections]
    if missing:
        raise RuntimeError(
            f"Contenu invalide : sections manquantes pour ids = {missing[:5]}."
        )

    meta = data.get("meta") or {}
    if not isinstance(meta, dict):
        raise RuntimeError("Contenu invalide : meta doit être un objet.")
    if not str(meta.get("page_title") or "").strip():
        raise RuntimeError("Contenu invalide : meta.page_title manquant.")
    if not str(meta.get("meta_description") or "").strip():
        raise RuntimeError("Contenu invalide : meta.meta_description manquant.")


def validate_description_payload(data: dict[str, Any]) -> None:
    """
    Validation legacy pour la description combinée architecture+content.
    Conservée pour compatibilité avec refinement_tool.
    """
    if not isinstance(data, dict):
        raise RuntimeError("Description invalide : payload non dict.")

    sections = data.get("sections")
    if not isinstance(sections, list) or len(sections) < REQUIRED_SECTIONS_MIN:
        raise RuntimeError(
            f"Description invalide : il faut au moins {REQUIRED_SECTIONS_MIN} sections "
            f"(recu: {len(sections) if isinstance(sections, list) else 0})."
        )

    animations = data.get("animations")
    if not isinstance(animations, list) or len(animations) < REQUIRED_ANIMATIONS_MIN:
        raise RuntimeError(
            f"Description invalide : il faut au moins {REQUIRED_ANIMATIONS_MIN} animations "
            f"(recu: {len(animations) if isinstance(animations, list) else 0})."
        )


def validate_html_output(html: str) -> dict[str, int]:
    validate_html_document(html)
    _validate_navigation_integrity(html)
    _validate_contact_privacy_integrity(html)
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
_UNSAFE_WINDOW_NAV_RE = re.compile(
    r"(window\.location\s*=|location\.href\s*=|location\.assign\s*\(|location\.replace\s*\()\s*(?!['\"](?:mailto:|tel:))",
    re.IGNORECASE,
)
_WINDOW_HREF_VAR_ASSIGN_RE = re.compile(
    r"(?:window\.)?location\.href\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*;",
    re.IGNORECASE,
)
_VAR_MAILTO_TEL_CONSTRUCTION_RE = re.compile(
    r"(?:var|let|const)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*['\"](?:mailto:|tel:)",
    re.IGNORECASE,
)
_PLACEHOLDER_IMG_HOST_RE = re.compile(
    r"(via\.placeholder\.com|placehold\.co|placeholder\.com|dummyimage\.com)",
    re.IGNORECASE,
)
_PLATFORM_EMAIL_RE = re.compile(r"(brand\s*ai|brandai|support@brandai)", re.IGNORECASE)
_EMAIL_TEXT_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)


def _is_external_href(href: str) -> bool:
    return href.startswith(("http://", "https://", "mailto:", "tel:"))


def _validate_navigation_integrity(html: str) -> None:
    lower = html.lower()
    # Autorise les redirections explicites vers mailto:/tel: (contact),
    # mais bloque toute autre navigation via window.location/location.href.
    has_unsafe_nav = bool(_UNSAFE_WINDOW_NAV_RE.search(lower))
    if has_unsafe_nav:
        allowed_vars = {
            m.group(1).lower()
            for m in _VAR_MAILTO_TEL_CONSTRUCTION_RE.finditer(html)
            if m.group(1)
        }
        href_assignments = [
            m.group(1).lower()
            for m in _WINDOW_HREF_VAR_ASSIGN_RE.finditer(html)
            if m.group(1)
        ]
        has_only_allowed_href_assignments = (
            bool(href_assignments)
            and all(var_name in allowed_vars for var_name in href_assignments)
        )
        if not has_only_allowed_href_assignments:
            raise RuntimeError(
                "Navigation invalide : script de redirection detecte (window.location/location.href). "
                "Utiliser des ancres internes #id pour nav/CTA. "
                "Seuls mailto:/tel: sont autorises pour les interactions de contact."
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


def _validate_contact_privacy_integrity(html: str) -> None:
    lower = html.lower()
    if "/website/contact-form" in lower or "__brandai_backend_url__" in lower:
        raise RuntimeError(
            "Contact invalide : formulaire relaye via backend detecte. "
            "Le site vitrine doit envoyer directement vers l'email du proprietaire (mailto:)."
        )

    # Supporte la variable historique (__BRANDAI_CONTACT_EMAIL__) et la nouvelle
    # variable simple/source unique (__SITE_OWNER_EMAIL__).
    configured_email = ""
    for pattern in (
        r"__SITE_OWNER_EMAIL__\s*=\s*['\"]([^'\"]+)['\"]",
        r"__BRANDAI_CONTACT_EMAIL__\s*=\s*['\"]([^'\"]+)['\"]",
    ):
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match and (match.group(1) or "").strip():
            configured_email = (match.group(1) or "").strip()
            break

    if configured_email and _PLATFORM_EMAIL_RE.search(configured_email):
        raise RuntimeError(
            "Contact invalide : adresse email plateforme detectee pour le formulaire. "
            "Utiliser l'email du proprietaire du site."
        )

    # Cohérence stricte : si l'email propriétaire est défini, toutes les
    # occurrences mailto: / emails visibles doivent être alignées pour éviter
    # les cas "support@ancien-domaine" restés dans le HTML.
    if configured_email:
        owner = configured_email.lower()

        mailto_targets = [
            (h.split("?", 1)[0][7:] or "").strip().lower()
            for h in _HREF_RE.findall(html)
            if h.lower().startswith("mailto:")
        ]
        mismatched_mailto = [e for e in mailto_targets if e and e != owner]
        if mismatched_mailto:
            sample = ", ".join(mismatched_mailto[:3])
            raise RuntimeError(
                "Contact invalide : des liens mailto utilisent un email different de __SITE_OWNER_EMAIL__ "
                f"({sample})."
            )

        visible_emails = {
            e.lower() for e in _EMAIL_TEXT_RE.findall(html) if "@" in e
        }
        # Ignore les emails potentiels dans scripts non liés ; on applique quand même
        # un contrôle strict pour forcer la cohérence globale du site vitrine.
        mismatched_visible = [e for e in visible_emails if e != owner]
        if mismatched_visible:
            sample = ", ".join(sorted(mismatched_visible)[:3])
            raise RuntimeError(
                "Contact invalide : des emails visibles ne correspondent pas a __SITE_OWNER_EMAIL__ "
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

