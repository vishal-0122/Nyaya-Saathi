from ddgs import DDGS

def search_cases(query: str) -> list[dict]:
    """
    Uses duckduckgo-search package to fetch top 3 news/case headlines with links.
    """
    keywords = ["accident", "injury", "hit", "run", "traffic", "road", "vehicle", "car", "bike"]
    if any(word in query.lower() for word in keywords):
        search_query = "road accident legal case India"
    else:
        search_query = f"{query} legal case India"

    results = []
    with DDGS() as ddgs:
        for r in ddgs.news(search_query, region="in-en", max_results=3):
            results.append({
                "headline": r["title"],
                "url": r["url"]
            })
    # Fallback to web search if news is empty
        if not results:
            for r in ddgs.text(search_query, region="in-en", max_results=3):
                results.append({
                    "headline": r["title"],
                    "url": r["href"]
                })

    # After collecting results
    filtered_results = [ 
        r for r in results if ".in" in r["url"] or "indiatimes" in r["url"] or "barandbench" in r["url"]
    ]
    if filtered_results:
        return filtered_results
    else:
        return results  # fallback to whatever was found

    # return results
