"""
Helpers Phase 3 / Phase 4 — extraction et validation du HTML généré.

Le LLM peut renvoyer :
- du HTML brut commençant par `<!DOCTYPE html>` (idéal),
- ou du HTML enveloppé dans des fences ```html ... ```,
- ou du HTML précédé / suivi d'un peu de prose explicative.

`extract_html_document` ramène toujours un document HTML propre.
`validate_html_document` lève une RuntimeError si le résultat n'est pas un site exploitable.
"""

from __future__ import annotations

import re

from config.website_builder_config import HTML_MIN_LENGTH, HTML_REQUIRED_MARKERS


_FENCE_RE = re.compile(r"```(?:html|HTML)?\s*([\s\S]*?)```", re.MULTILINE)
_DOCTYPE_RE = re.compile(r"<!DOCTYPE\s+html", re.IGNORECASE)


def extract_html_document(raw: str) -> str:
    """Renvoie un document HTML nettoyé à partir d'une réponse LLM."""
    if not raw:
        raise RuntimeError("Le modèle n'a renvoyé aucun contenu.")

    text = raw.strip()

    # 1) Si on a au moins un bloc fenced ```html ... ```, on prend le plus volumineux.
    fenced = _FENCE_RE.findall(text)
    if fenced:
        candidate = max((f.strip() for f in fenced), key=len, default="")
        if candidate:
            return _trim_to_html_bounds(candidate)

    # 2) Sinon, on essaie de couper au DOCTYPE puis à </html>.
    return _trim_to_html_bounds(text)


def _trim_to_html_bounds(text: str) -> str:
    text = text.strip()

    doctype = _DOCTYPE_RE.search(text)
    if doctype:
        text = text[doctype.start():]
    else:
        # pas de doctype → on cherche le premier <html>
        idx = text.lower().find("<html")
        if idx >= 0:
            text = text[idx:]

    end = text.lower().rfind("</html>")
    if end >= 0:
        text = text[: end + len("</html>")]

    return text.strip()


def validate_html_document(html: str) -> None:
    if not html or len(html) < HTML_MIN_LENGTH:
        raise RuntimeError(
            f"HTML généré trop court ({len(html or '')} caractères). "
            f"Minimum attendu : {HTML_MIN_LENGTH}."
        )
    lower = html.lower()
    missing = [m for m in HTML_REQUIRED_MARKERS if m not in lower]
    if missing:
        raise RuntimeError(
            "Document HTML invalide : marqueurs manquants → " + ", ".join(missing)
        )


def html_stats(html: str) -> dict[str, int]:
    """Petites métriques utiles pour les logs / réponses API."""
    return {
        "length": len(html or ""),
        "approx_lines": (html or "").count("\n") + 1,
    }
