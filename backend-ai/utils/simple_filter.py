def simple_filter(items, max_items=8, max_chars=300):
    if not items:
        return []

    results = []

    for item in items:
        title = (item.get("title") or "").strip()
        snippet = (item.get("snippet") or "").strip()

        # ignorer snippets trop courts
        if len(snippet) < 30:
            continue

        # ignorer snippets bruités
        if snippet.lower().startswith(("stated", "pt using", "de access", "ave to")):
            continue

        results.append({
            "title": title[:120],
            "snippet": snippet[:max_chars],
            "url": item.get("url", "")
        })

        if len(results) >= max_items:
            break

    return results
