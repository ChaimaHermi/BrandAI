"""
Test manuel GNews API v4 — à lancer depuis backend-ai/ :
  python test_gnews.py
"""
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

API_KEY = (os.getenv("GNEWS_API_KEY") or os.getenv("GNEWSAPI_KEY") or "").strip()
if not API_KEY:
    raise SystemExit("GNEWS_API_KEY manquant — vérifie Brand AI/.env")

url = "https://gnews.io/api/v4/search"

def run(label: str, params: dict) -> None:
    p = {"apikey": API_KEY, **params}
    r = requests.get(url, params=p, timeout=20)
    print(f"\n=== {label} ===")
    print("STATUS:", r.status_code)
    data = r.json()
    articles = data.get("articles") or []
    print("totalArticles:", data.get("totalArticles", len(articles)))
    for i, a in enumerate(articles[:3], 1):
        print(f"  {i}. {a.get('title', '')[:80]}")
        print(f"     source: {a.get('source', {}).get('name', '')} | {a.get('publishedAt', '')[:10]}")

# Sans aucun filtre country — juste q + lang + max
run("1. EdTech",
    {"q": "EdTech education technology", "lang": "en", "max": 5})

run("2. Healthy food",
    {"q": "healthy food snacks", "lang": "en", "max": 5})

run("3. Livraison repas",
    {"q": "food delivery app", "lang": "en", "max": 5})

run("4. Chips végétales",
    {"q": "vegetable chips vegan", "lang": "en", "max": 5})

run("5. Tunisie startup",
    {"q": "Tunisia startup", "lang": "en", "max": 5})

run("6. Productivité étudiante",
    {"q": "student productivity app", "lang": "en", "max": 5})