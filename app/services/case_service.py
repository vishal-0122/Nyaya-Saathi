import logging
from ddgs import DDGS

logger = logging.getLogger(__name__)

def search_cases(query: str) -> list[dict]:
    """
    Fetch top relevant legal/news cases using DuckDuckGo.
    Returns a list of dicts with 'headline' and 'url'.
    """

    try:
        # -----------------------------
        # 🔍 Query Normalization
        # -----------------------------
        keywords = [
            "accident", "injury", "hit", "run",
            "traffic", "road", "vehicle", "car", "bike"
        ]

        if any(word in query.lower() for word in keywords):
            search_query = "road accident legal case India"
        else:
            search_query = f"{query} legal case India"

        results = []

        # -----------------------------
        # 📰 News Search
        # -----------------------------
        with DDGS() as ddgs:
            for r in ddgs.news(search_query, region="in-en", max_results=3):
                results.append({
                    "headline": r.get("title", ""),
                    "url": r.get("url", "")
                })

            # -----------------------------
            # 🔁 Fallback: Web Search
            # -----------------------------
            if not results:
                for r in ddgs.text(search_query, region="in-en", max_results=3):
                    results.append({
                        "headline": r.get("title", ""),
                        "url": r.get("href", "")
                    })

        # -----------------------------
        # 🇮🇳 Filter Indian Sources
        # -----------------------------
        filtered_results = [
            r for r in results
            if (
                ".in" in r["url"]
                or "indiatimes" in r["url"]
                or "barandbench" in r["url"]
            )
        ]

        if filtered_results:
            return filtered_results

        return results

    except Exception as e:
        logger.exception("Case search failed")

        # -----------------------------
        # 🔥 SAFE FALLBACK
        # -----------------------------
        return [
            {
                "headline": "No recent cases found. Please verify manually.",
                "url": ""
            }
        ]