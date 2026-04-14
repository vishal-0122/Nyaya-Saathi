import re
import logging
from typing import Tuple, Optional, List, Dict

from app.db.postgres.queries import get_lawyers_by_location

logger = logging.getLogger(__name__)


def extract_location_and_count_from_query(query: str) -> Tuple[Optional[str], Optional[int]]:
    if not query:
        return None, None

    count = None

    # 🔢 Extract numeric count
    count_match = re.search(r"(\d+)\s+lawyers?", query, re.IGNORECASE)
    if count_match:
        count = int(count_match.group(1))
    else:
        if re.search(r"some\s+lawyers?", query, re.IGNORECASE):
            count = 5
        elif re.search(r"few\s+lawyers?", query, re.IGNORECASE):
            count = 3

    # 📍 Extract location
    match = re.search(r"(?:from|in)\s+([A-Za-z\s]+)", query, re.IGNORECASE)
    city = None

    if match:
        city = match.group(1).strip()
        city = re.sub(r"\b(city|town|village)\b", "", city, flags=re.IGNORECASE).strip()

    return city if city else None, count


def find_lawyers(query: str) -> List[Dict]:
    try:
        location, count = extract_location_and_count_from_query(query)

        logger.info(f"Lawyer lookup → location: {location}, count: {count}")

        lawyers = get_lawyers_by_location(location, limit=count)

        return lawyers or []

    except Exception:
        logger.exception("Lawyer lookup failed")

        return []