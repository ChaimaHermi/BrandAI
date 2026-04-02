import os
import httpx
import re
from typing import Dict, Any, List

BRANDFETCH_API_KEY = os.getenv("BRANDFETCH_API_KEY")


# ─────────────────────────────────────────
# NAME NORMALIZATION
# ─────────────────────────────────────────
def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").strip().lower())
    # "DailyBooster" → "dailybooster"
    # "Train Flow"   → "trainflow"
    # "CoachNest"    → "coachnest"


# ─────────────────────────────────────────
# BRAND NAME CHECK
# ─────────────────────────────────────────
def label_in_brand(label: str, brand: dict) -> bool:
    label = _normalize_name(label)
    brand_name = _normalize_name(brand.get("name") or "")

    if not brand_name:
        return False

    # ✅ correspondance exacte uniquement
    return label == brand_name


# ─────────────────────────────────────────
# PUBLIC CHECK (1 seul appel API)
# ─────────────────────────────────────────
async def check_brand_name(name: str) -> Dict[str, Any]:
    label = _normalize_name(name)

    if not label:
        return {"name": name, "exists": False, "matched_name": None}

    url = f"https://api.brandfetch.io/v2/search/{label}"
    headers = {"Authorization": f"Bearer {BRANDFETCH_API_KEY}"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                brands = response.json()

                for brand in brands:
                    if label_in_brand(label, brand):
                        return {
                            "name": name,
                            "exists": True,
                            "matched_name": brand.get("name")  
                        }

        except Exception:
            pass

    return {"name": name, "exists": False, "matched_name": None}


# ─────────────────────────────────────────
# BULK VALIDATION
# ─────────────────────────────────────────
async def validate_name_list(names: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    results = []

    for item in names:
        name = item.get("name")

        if not name:
            continue

        check = await check_brand_name(name)

        item["availability"] = (
            "exists" if check["exists"] else "not_exists"
        )

        item["matched_name"] = check.get("matched_name") 

        results.append(item)

    return results