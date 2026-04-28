from __future__ import annotations

import os
import tempfile
from pathlib import Path


def _resolve_google_credentials_path() -> str:
    explicit = (os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or "").strip()
    if explicit:
        return explicit
    local = (Path(__file__).resolve().parents[2] / "google_key.json").as_posix()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = local
    return local


def verifier_originalite_logo(image_path: str, *, max_similar: int = 2) -> bool:
    """
    Vérifie l'originalité via Google Cloud Vision Web Detection.
    Retourne False si le nombre d'images visuellement similaires > max_similar.
    """
    try:
        _resolve_google_credentials_path()
        from google.cloud import vision

        client = vision.ImageAnnotatorClient()
        with open(image_path, "rb") as f:
            content = f.read()

        image = vision.Image(content=content)
        response = client.web_detection(image=image)
        if response.error.message:
            return False

        similar = list((response.web_detection.visually_similar_images or []))
        return len(similar) <= max_similar
    except Exception:
        return False


def verifier_originalite_logo_bytes(
    image_bytes: bytes,
    *,
    suffix: str = ".png",
    max_similar: int = 2,
) -> bool:
    fd, path = tempfile.mkstemp(prefix="brandai-logo-", suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(image_bytes or b"")
        return verifier_originalite_logo(path, max_similar=max_similar)
    finally:
        try:
            os.remove(path)
        except Exception:
            pass
