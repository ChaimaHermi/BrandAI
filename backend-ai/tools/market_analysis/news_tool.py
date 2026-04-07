import requests
import os

NEWS_API_KEY = os.getenv("NEWSAPI_KEY")

def news_search(query: str):
    url = "https://newsapi.org/v2/everything"

    params = {
        "q": query,
        "apiKey": NEWS_API_KEY,
        "pageSize": 5
    }

    res = requests.get(url, params=params)
    data = res.json()

    results = []

    for article in data.get("articles", []):
        results.append({
            "title": article.get("title"),
            "description": article.get("description"),
            "url": article.get("url")
        })

    return results