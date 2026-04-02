import os
import httpx
import re
import asyncio
from typing import Dict, Any, List

from config.branding_config import DOMAIN_SUFFIXES, DOMAIN_VARIANTS

BRANDFETCH_API_KEY = os.getenv("BRANDFETCH_API_KEY")


# ─────────────────────────────────────────
# DOMAIN NORMALIZATION (regex)
# ─────────────────────────────────────────
_DOMAIN_ALLOWED_RE = re.compile(r"[^a-z0-9-]")
_DOMAIN_DASH_TRIM_RE = re.compile(r"^-+|-+$")


def _to_domain_label(name: str) -> str:
    """
    Convertit un nom de marque en label de domaine:
    - lower
    - espaces -> '-'
    - supprime tout sauf [a-z0-9-] via regex
    - trim des tirets en début/fin
    """
    s = (name or "").strip().lower()
    s = s.replace(" ", "-")
    s = _DOMAIN_ALLOWED_RE.sub("", s)
    s = _DOMAIN_DASH_TRIM_RE.sub("", s)
    s = re.sub(r"-{2,}", "-", s)
    return s[:63]  # limite label DNS


# ─────────────────────────────────────────
# CORE: CHECK SINGLE DOMAIN
# ─────────────────────────────────────────
async def _check_domain(domain: str) -> Dict[str, Any]:
    url = f"https://api.brandfetch.io/v2/brands/{domain}"

    headers = {
        "Authorization": f"Bearer {BRANDFETCH_API_KEY}"
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                return {
                    "exists": True,
                    "domain": domain,
                    "data": response.json()
                }

            if response.status_code == 404:
                return {
                    "exists": False,
                    "domain": domain
                }

            return {
                "exists": None,
                "domain": domain,
                "error": response.text
            }

        except Exception as e:
            return {
                "exists": None,
                "domain": domain,
                "error": str(e)
            }


# ─────────────────────────────────────────
# PUBLIC: CHECK BRAND NAME (MULTI DOMAIN)
# ─────────────────────────────────────────
async def check_brand_name(name: str) -> Dict[str, Any]:
    """
    Check if brand exists using multiple domains.
    """

    label = _to_domain_label(name)
    if not label:
        return {
            "name": name,
            "exists": None,
            "matched_domain": None,
            "error": "invalid_domain_label",
        }

    suffixes = DOMAIN_SUFFIXES or ["com", "io", "tn"]
    variants = DOMAIN_VARIANTS or ["{label}"]

    # Variantes (studyfit, getstudyfit, studyfitnotes, ...)
    candidate_labels = []
    for tpl in variants:
        try:
            v = (tpl or "{label}").format(label=label)
        except Exception:
            v = label
        v = _to_domain_label(v)
        if v and v not in candidate_labels:
            candidate_labels.append(v)

    # Domaines finaux: label + suffix (supporte "co.za")
    domains = [f"{lab}.{suf}" for lab in candidate_labels for suf in suffixes]

    # Brandfetch peut être lent → paralléliser avec limite de concurrence.
    # Dès qu'on trouve un domaine existant, on short-circuit.
    sem = asyncio.Semaphore(8)

    async def _bounded_check(d: str):
        async with sem:
            return d, await _check_domain(d)

    tasks = [asyncio.create_task(_bounded_check(d)) for d in domains]
    try:
        for fut in asyncio.as_completed(tasks):
            domain, result = await fut
            if result.get("exists") is True:
                for t in tasks:
                    t.cancel()
                return {
                    "name": name,
                    "exists": True,
                    "matched_domain": domain,
                }
    finally:
        for t in tasks:
            if not t.done():
                t.cancel()

    return {
        "name": name,
        "exists": False,
        "matched_domain": None
    }


# ─────────────────────────────────────────
# BULK CHECK (RECOMMENDED)
# ─────────────────────────────────────────
async def validate_name_list(names: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add availability field to each name option.
    """

    results = []

    for item in names:
        name = item.get("name")

        if not name:
            continue

        check = await check_brand_name(name)

        item["availability"] = (
            "taken" if check["exists"] else "likely_available"
        )

        item["matched_domain"] = check.get("matched_domain")

        results.append(item)

    return results