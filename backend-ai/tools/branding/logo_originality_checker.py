from __future__ import annotations

import asyncio
import logging
import os

logger = logging.getLogger("brandai.logo_originality")

_SERPAPI_URL = "https://serpapi.com/search.json"

# Cache session : si quota SerpApi épuisé ou erreur fatale, on arrête les appels
_api_disabled: bool = False


async def verifier_originalite_logo_bytes(
    image_bytes: bytes,
    *,
    max_similar: int = 2,
) -> tuple[bool, list[str]]:
    """
    Vérifie l'originalité du logo via SerpApi Google Lens (reverse image search).

    Flow :
      1. Upload image bytes sur Cloudinary → URL publique
      2. SerpApi Google Lens → visual_matches
      3. is_original = True si visual_matches <= max_similar

    Nécessite SERPAPI_KEY dans .env.
    Si clé absente / quota épuisé / erreur → retourne (True, []) sans bloquer.
    """
    global _api_disabled

    if _api_disabled:
        logger.debug("[originality] SerpApi désactivé (erreur précédente) — vérification ignorée")
        return True, []

    api_key = (os.getenv("SERPAPI_KEY") or "").strip()
    if not api_key:
        logger.warning("[originality] SERPAPI_KEY absent dans .env — vérification ignorée")
        return True, []

    if not image_bytes:
        return True, []

    try:
        import httpx
    except ImportError:
        logger.warning("[originality] httpx non installé — vérification ignorée")
        return True, []

    # ── 1. Upload sur Cloudinary pour obtenir une URL publique ───────────────
    try:
        from tools.content_generation.cloudinary_upload import upload_image_bytes
        image_url = await asyncio.to_thread(
            upload_image_bytes,
            image_bytes,
            mime="image/png",
            folder="brandai/logo-originality",
        )
        logger.info("[originality] Image uploadée → %s", image_url[:80])
    except Exception as exc:
        logger.warning("[originality] Upload Cloudinary échoué : %s — vérification ignorée", exc)
        return True, []

    # ── 2. SerpApi Google Lens ───────────────────────────────────────────────
    params = {
        "engine": "google_lens",
        "url": image_url,
        "api_key": api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(_SERPAPI_URL, params=params)

        # Quota épuisé ou clé invalide
        if resp.status_code == 401:
            _api_disabled = True
            logger.error(
                "[originality] ❌ SerpApi — clé invalide (401). "
                "Vérifiez SERPAPI_KEY dans .env. Vérification désactivée pour cette session."
            )
            return True, []

        if resp.status_code == 429:
            _api_disabled = True
            logger.error(
                "[originality] ❌ SerpApi — quota mensuel épuisé (429). "
                "Vérification désactivée pour cette session. "
                "Renouvelez votre quota sur https://serpapi.com/manage-api-key"
            )
            return True, []

        if not resp.is_success:
            logger.warning(
                "[originality] SerpApi HTTP %d — vérification ignorée", resp.status_code
            )
            return True, []

        data = resp.json()

        # Vérifier si SerpApi retourne une erreur applicative
        if "error" in data:
            err_msg = data["error"]
            if "credit" in err_msg.lower() or "plan" in err_msg.lower() or "quota" in err_msg.lower():
                _api_disabled = True
                logger.error(
                    "[originality] ❌ SerpApi quota épuisé : %s. "
                    "Vérification désactivée pour cette session.",
                    err_msg,
                )
            else:
                logger.warning("[originality] SerpApi erreur : %s — vérification ignorée", err_msg)
            return True, []

        # visual_matches = images visuellement similaires trouvées sur le web
        visual_matches = data.get("visual_matches") or []
        similar_urls = [m.get("link") or m.get("thumbnail", "") for m in visual_matches if isinstance(m, dict)]
        similar_urls = [u for u in similar_urls if u]

        is_original = len(visual_matches) <= max_similar
        logger.info(
            "[originality] ✓ SerpApi Google Lens — similaires=%d  seuil=%d  →  original=%s",
            len(visual_matches), max_similar, is_original,
        )
        return is_original, similar_urls

    except Exception as exc:
        logger.warning("[originality] Erreur inattendue SerpApi : %s — vérification ignorée", exc)
        return True, []
