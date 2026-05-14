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

from config.website_builder_config import (
    HTML_MIN_LENGTH,
    HTML_REQUIRED_MARKERS,
    HTML_STRICT_VALIDATION,
)


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


def repair_html_document(html: str) -> str:
    """
    Répare un HTML tronqué par une limite de tokens.
    Ferme les balises manquantes dans l'ordre inverse logique.
    Appelé avant validate_html_document.
    """
    if not html:
        return html
    lower = html.lower()

    # Ferme les balises ouvertes les plus courantes si elles manquent
    # Ordre important : du plus profond au plus haut dans l'arbre
    repairs = [
        ("</section>",  "<section"),
        ("</main>",     "<main"),
        ("</nav>",      "<nav"),
        ("</header>",   "<header"),
        ("</footer>",   "<footer"),
        ("</div>",      None),   # trop générique, on skip le count ici
        ("</body>",     "<body"),
        ("</html>",     "<html"),
    ]

    appended: list[str] = []
    for closing_tag, opening_tag in repairs:
        if closing_tag == "</div>":
            continue  # skip les div (trop nombreuses, fausserait la réparation)
        if opening_tag and opening_tag in lower and closing_tag.lower() not in lower:
            appended.append(closing_tag)
            lower += closing_tag  # mise à jour pour les vérifications suivantes

    if appended:
        import logging
        logging.getLogger("brandai.website_builder.renderer").warning(
            "[website_renderer] HTML tronqué détecté — balises ajoutées : %s",
            ", ".join(appended),
        )
        html = html.rstrip() + "\n" + "\n".join(appended)

    return html


def validate_html_document(html: str) -> None:
    if not html or not html.strip():
        raise RuntimeError("Document HTML vide : aucune sortie exploitable à sauvegarder.")

    if not HTML_STRICT_VALIDATION:
        return

    if len(html) < HTML_MIN_LENGTH:
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
