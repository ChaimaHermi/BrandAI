def simple_filter(items, max_items=8, max_chars=300):
    if not items:
        return []

    results = []
    for item in items[:max_items]:
        results.append({
            "title": (item.get("title") or "")[:120],
            "snippet": (item.get("snippet") or "")[:max_chars],
            "url": item.get("url", "")
        })
    return results
