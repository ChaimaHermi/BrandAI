"""Parse JSON LLM (fences ```) + normalisation des listes pour KeywordBundle."""

from __future__ import annotations

import json
import re


def parse_keyword_json_response(raw: str) -> dict:
    cleaned = re.sub(r"```json\s*", "", raw, flags=re.IGNORECASE)
    cleaned = re.sub(r"```\s*", "", cleaned)
    return json.loads(cleaned.strip())


def norm_str_list(val, *, max_len: int | None) -> list[str]:
    if not isinstance(val, list):
        return []
    out = [str(x).strip() for x in val if str(x).strip()]
    return out[:max_len] if max_len is not None else out
