import re
from app.db.postgres.queries import get_lawyers_by_location


def extract_location_and_count_from_query(query: str) -> tuple[str | None, int | None]:
    print(f"[DEBUG] Raw query for location/count extraction: {query}")
    if not query:
        return None, None
    # Extract count: e.g., '5 lawyers', 'some lawyers', 'few lawyers'
    count = None
    count_match = re.search(r"(\d+)\s+lawyers?", query, re.IGNORECASE)
    if count_match:
        count = int(count_match.group(1))
    else:
        # Handle 'some lawyers', 'few lawyers', etc.
        if re.search(r"some\s+lawyers?", query, re.IGNORECASE):
            count = 5
        elif re.search(r"few\s+lawyers?", query, re.IGNORECASE):
            count = 3
    # Extract location
    match = re.search(r"(?:from|in)\s+([A-Za-z\s]+)", query, re.IGNORECASE)
    city = None
    if match:
        city = match.group(1).strip()
        city = re.sub(r"\b(city|town|village)\b", "", city, flags=re.IGNORECASE).strip()
        print(f"[DEBUG] Extracted city: '{city}'")
    return city if city else None, count

def find_lawyers(query: str) -> list[dict]:
    """
    Extracts location and count from query and returns a list of lawyers for that location, up to the requested count.
    """
    location, count = extract_location_and_count_from_query(query)
    print(f"[DEBUG] Passing location '{location}' and count '{count}' to DB")
    lawyers = get_lawyers_by_location(location, limit=count)
    print(f"[DEBUG] Lawyers returned from DB: {lawyers}")
    return lawyers
