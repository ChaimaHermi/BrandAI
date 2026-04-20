import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx


def project_root_from_test_file(test_file: str) -> Path:
    # tests/social_optimizer/<file>.py -> backend-ai/
    return Path(test_file).resolve().parent.parent.parent


async def print_connect_message(platform_label: str, oauth_path: str) -> None:
    base = (os.getenv("BRANDAI_AI_BASE_URL") or "http://localhost:8001").rstrip("/")
    fallback = f"{base}{oauth_path}"
    oauth_url = fallback
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(fallback)
            data = response.json() if response.content else {}
            oauth_url = data.get("url") or fallback
    except Exception:
        oauth_url = fallback
    print(f"\nCONNECT FIRST ({platform_label}): {oauth_url}\n")


def write_result_json(test_file: str, filename: str, payload: dict[str, Any]) -> Path:
    out_dir = Path(test_file).resolve().parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    output = dict(payload)
    output["collected_at"] = datetime.now(timezone.utc).isoformat()
    out_path = out_dir / filename
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved: {out_path}\n")
    return out_path

