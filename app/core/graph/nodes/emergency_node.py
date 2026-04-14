from app.mcp.tools.emergency_services import emergency_services_tool
import re
from langsmith import traceable


def _extract_location(text: str) -> str:
    match = re.search(r"(?:in|from|at|near|around|within)\s+([A-Za-z\s]+)", text or "", re.IGNORECASE)
    if match:
        return match.group(1).strip().rstrip(".,")
    return ""

@traceable(name="emergency_node", run_type="tool")
def emergency_node(state: dict):

    plan = state.get("plan", {})
    location = state.get("location") or plan.get("location", "")
    conversation_context = state.get("conversation_context", "") or ""
    combined_text = f"{state.get('query', '')}\n{conversation_context}"

    if not location:
        location = _extract_location(combined_text)

    # Always detect service_type from query + context
    query = combined_text.lower()
    if any(k in query for k in ["hospital", "injury", "ambulance", "doctor", "medical", "nearest hospital"]):
        service_type = "hospital"
    elif any(k in query for k in ["police", "theft", "crime", "robbery", "assault", "nearest police", "police station"]):
        service_type = "police"
    else:
        service_type = "hospital"  # default fallback

    try:
        services = emergency_services_tool(location, service_type)
        state["emergency_services"] = services if services else []
        state["emergency_error"] = ""
    except Exception as e:
        state["emergency_services"] = []
        state["emergency_error"] = str(e)
    return state
