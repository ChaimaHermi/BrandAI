"""Test rapide des cles NVIDIA_API_KEY_* depuis .env (prompt: bonjour)."""
import json
import os
import re
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

URL = "https://integrate.api.nvidia.com/v1/chat/completions"


def collect_keys() -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    seen: set[str] = set()

    for i in range(1, 9):
        name = f"NVIDIA_API_KEY_{i}"
        val = (os.getenv(name) or "").strip()
        if val and val not in seen:
            seen.add(val)
            found.append((name, val))

    for name, val in sorted(os.environ.items()):
        if not re.search(r"NVIDIA.*KEY", name, re.I):
            continue
        v = (val or "").strip()
        if len(v) < 10 or v in seen:
            continue
        seen.add(v)
        found.append((name, v))

    return found


def main() -> None:
    keys = collect_keys()
    print(f"Cles NVIDIA trouvees: {len(keys)}")
    if not keys:
        print("ERREUR: aucune NVIDIA_API_KEY_* dans .env")
        raise SystemExit(1)

    body = {
        "model": "openai/gpt-oss-120b",
        "messages": [{"role": "user", "content": "Reponds en une phrase courte: bonjour"}],
        "max_tokens": 64,
        "temperature": 0.2,
    }

    for label, key in keys:
        suffix = key[-6:] if len(key) >= 6 else "???"
        print(f"\n--- {label} (...{suffix}) ---")
        t0 = time.perf_counter()
        try:
            with httpx.Client(timeout=120.0) as client:
                r = client.post(
                    URL,
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
            elapsed = time.perf_counter() - t0
            print(f"HTTP {r.status_code} en {elapsed:.1f}s")
            if r.status_code != 200:
                print("Body:", (r.text or "")[:300])
                continue
            data = r.json()
            msg = data.get("choices", [{}])[0].get("message", {})
            content = (msg.get("content") or msg.get("reasoning_content") or "").strip()
            if content:
                preview = content[:200].replace("\n", " ")
                print("OK - reponse:", preview)
            else:
                print("ATTENTION: 200 mais contenu vide. message keys:", list(msg.keys()))
                print("raw:", json.dumps(data)[:500])
        except Exception as e:
            elapsed = time.perf_counter() - t0
            print(f"ECHEC apres {elapsed:.1f}s: {type(e).__name__}: {str(e)[:200]}")


if __name__ == "__main__":
    main()
