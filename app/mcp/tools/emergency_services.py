import os
import requests
from typing import List, Dict

# Nominatim does not require an API key, but we'll use an environment variable for the User-Agent
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = os.getenv("NOMINATIM_USER_AGENT", "nyaya-saathi-app/1.0")

SERVICE_TYPE_MAP = {
    "police": "police",
    "hospital": "hospital"
}


def _normalize_text(value: str) -> str:
    """Normalize text by lowercasing, removing extra whitespace, and state codes."""
    normalized = " ".join(str(value or "").lower().split())
    # Remove state code patterns like "in-mh" (country-state code)
    normalized = normalized.replace("in-mh", "").replace("in-", "")
    # Clean up extra spaces that might result from removal
    normalized = " ".join(normalized.split())
    return normalized


def _extract_postal_code(address: str) -> str:
    """Extract postal code (usually 6 digits in India) from address."""
    import re
    matches = re.findall(r'\b\d{6}\b', address or "")
    return matches[0] if matches else ""


def _short_name(display_name: str, address_text: str) -> str:
    name = str(display_name or "").strip()
    address = str(address_text or "").strip()
    if name and address and name.lower().startswith(address.lower()):
        return name[: len(name) - len(address)].rstrip(", ") or name
    return name

def emergency_services_tool(location: str, service_type: str) -> List[Dict[str, str]]:
    """
    Search for nearby emergency services (police or hospital) using Nominatim OpenStreetMap API.
    Returns a list of up to 10 dicts with 'name' and 'address'.
    """
    if service_type not in SERVICE_TYPE_MAP:
        raise ValueError("service_type must be 'police' or 'hospital'")

    headers = {"User-Agent": USER_AGENT}

    query_variants = [
        f"{SERVICE_TYPE_MAP[service_type]} in {location}",
        f"{SERVICE_TYPE_MAP[service_type]} near {location}",
        f"{SERVICE_TYPE_MAP[service_type]} {location}",
    ]

    for query in query_variants:
        try:
            params = {
                "q": query,
                "format": "jsonv2",
                "addressdetails": 1,
                "limit": 5,
                "countrycodes": "in"
            }
            response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            results = response.json()

            services = []
            seen = set()
            for place in results:
                raw_name = place.get("display_name", "")
                address = place.get("address", {})
                address_str = ", ".join([v for k, v in address.items() if v])
                name = _short_name(raw_name, address_str)
                # Use postal code + normalized name as dedup key for better accuracy
                postal_code = _extract_postal_code(address_str)
                dedupe_key = (_normalize_text(name), postal_code) if postal_code else (_normalize_text(name), _normalize_text(address_str))
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                services.append({
                    "name": name or raw_name,
                    "address": address_str,
                })

            if services:
                return services
        except Exception:
            continue

    # Structured fallback when live lookup is unavailable
    return [
        {
            "name": f"No live {service_type} results found",
            "address": f"Please try a nearby locality within {location} or retry after a moment."
        }
    ]
