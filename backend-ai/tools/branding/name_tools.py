import os
import re
import json
import asyncio
from pathlib import Path
import httpx
from langchain.tools import tool
from langsmith import traceable

from config.branding_config import NAME_EXISTS_MEMORY_MAX, NAME_SHORT_TERM_MEMORY_DIR
from prompts.branding.name_prompt import build_name_user_prompt

BRANDFETCH_API_KEY = os.getenv("BRANDFETCH_API_KEY")


# ─────────────────────────────────────────
# NAME NORMALIZATION
# ─────────────────────────────────────────
def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").strip().lower())


def _resolve_memory_file(idea_id: int | str | None) -> Path | None:
    if idea_id in (None, ""):
        return None
    root = Path(__file__).resolve().parents[2]  # backend-ai/
    memory_dir = root / NAME_SHORT_TERM_MEMORY_DIR
    memory_dir.mkdir(parents=True, exist_ok=True)
    return memory_dir / f"idea_{idea_id}_exists_names.json"


def _load_exists_memory(idea_id: int | str | None) -> list[str]:
    path = _resolve_memory_file(idea_id)
    if path is None or not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        names = data.get("exists_names", []) if isinstance(data, dict) else []
        if not isinstance(names, list):
            return []
        out: list[str] = []
        seen: set[str] = set()
        for n in names:
            norm = _normalize_name(str(n))
            if not norm or norm in seen:
                continue
            seen.add(norm)
            out.append(norm)
        return out[-NAME_EXISTS_MEMORY_MAX:]
    except Exception:
        return []


def _save_exists_memory(idea_id: int | str | None, exists_names: list[str]) -> None:
    path = _resolve_memory_file(idea_id)
    if path is None:
        return
    deduped: list[str] = []
    seen: set[str] = set()
    for n in exists_names:
        norm = _normalize_name(n)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        deduped.append(norm)
    deduped = deduped[-NAME_EXISTS_MEMORY_MAX:]
    payload = {
        "idea_id": idea_id,
        "exists_names": deduped,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_exists_memory(idea_id: int | str | None, names: list[str]) -> None:
    if not names:
        return
    current = _load_exists_memory(idea_id)
    merged = current + [str(n) for n in names]
    _save_exists_memory(idea_id, merged)


# ─────────────────────────────────────────
# BRAND NAME CHECK
# ─────────────────────────────────────────
def _label_in_brand(label: str, brand: dict) -> bool:
    label = _normalize_name(label)
    brand_name = _normalize_name(brand.get("name") or "")
    if not brand_name:
        return False
    return label == brand_name


# ─────────────────────────────────────────
# BRANDFETCH API CALL
# ─────────────────────────────────────────
@traceable(name="api.brandfetch_check", tags=["branding", "api", "brandfetch"])
async def _check_brand_name(name: str) -> dict:
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
                    if _label_in_brand(label, brand):
                        return {
                            "name": name,
                            "exists": True,
                            "matched_name": brand.get("name")
                        }
        except Exception:
            pass

    return {"name": name, "exists": False, "matched_name": None}


# ─────────────────────────────────────────
# TOOL 1 : GENERATE NAMES
# ─────────────────────────────────────────
def make_generate_names_tool(llm, idea: dict, *, idea_id: int | str | None = None):

    @traceable(name="tool.generate_names", tags=["branding", "tool", "name_generation"])
    def _generate(excluded_names_str: str) -> str:
        excluded_input = [n.strip() for n in excluded_names_str.split(",") if n.strip()]
        memory_exists = _load_exists_memory(idea_id)

        # Merge dynamic exclusions + short-term memory (exists only), dedup by normalized form
        excluded: list[str] = []
        seen: set[str] = set()
        for n in excluded_input + memory_exists:
            norm = _normalize_name(n)
            if not norm or norm in seen:
                continue
            seen.add(norm)
            excluded.append(norm)

        prompt = build_name_user_prompt(idea=idea, excluded_names=excluded)
        response = llm.invoke(prompt)
        return response.content

    @tool
    def generate_names(excluded_names_str: str) -> str:
        """
        Generates brand names (JSON with name_options) for the startup.
        Input: comma-separated blacklisted names to exclude, or empty string for first call.
        """
        return _generate(excluded_names_str)

    return generate_names


# ─────────────────────────────────────────
# TOOL 2 : VALIDATE NAMES
# ─────────────────────────────────────────
def make_validate_names_tool(*, idea_id: int | str | None = None):

    @traceable(name="tool.validate_names", tags=["branding", "tool", "brandfetch"])
    async def _validate(options: list) -> str:
        results = []
        exists_names: list[str] = []
        for item in options:
            name = item.get("name")
            if not name:
                continue
            check = await _check_brand_name(name)
            is_exists = bool(check["exists"])
            if is_exists:
                exists_names.append(str(name))
            results.append({
                "name": name,
                "description": item.get("description", ""),
                "availability": "exists" if is_exists else "not_exists",
                "matched_name": check.get("matched_name"),
            })
        _append_exists_memory(idea_id, exists_names)
        return json.dumps(results, ensure_ascii=False)

    @tool
    async def validate_names(
        names_json: str = "",
        name_options: list | None = None,
    ) -> str:
        """
        Checks if brand names already exist using Brandfetch API.
        Input accepted:
        - names_json: JSON string like {"name_options": [...]}
        - or name_options: direct list of objects [{"name":"...", "description":"..."}]
        Returns availability status for each name.
        """
        try:
            if isinstance(name_options, list) and name_options:
                options = name_options
            else:
                data = json.loads(names_json or "{}")
                options = data.get("name_options", [])
        except Exception:
            return json.dumps({"error": "invalid JSON input"})

        return await _validate(options)

    return validate_names