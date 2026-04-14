from langsmith import traceable


@traceable(name="suggestion_node", run_type="chain")
def suggestion_node(state: dict) -> dict:
    """
    Generates context-aware suggestions for helpful follow-up actions based on user intent and query.
    Sets state["suggestions"] as a list of strings.
    """
    intent = state.get("intent", "").lower()
    query = state.get("query", "")
    suggestions = []

    # Conversational, user-friendly suggestions (2–3 per context)
    if "accident" in query or "injury" in query:
        suggestions = [
            "Would you like contact details of nearby lawyers?",
            "Do you want help finding the nearest police station?",
            "Would you like help drafting a complaint?"
        ]
    elif "property" in query or "land" in query:
        suggestions = [
            "Would you like to check property records online?",
            "Do you want help finding the local land registry office?",
            "Would you like contact details of property lawyers?"
        ]
    elif "theft" in query or "stolen" in query:
        suggestions = [
            "Would you like to report the theft to the police online?",
            "Do you want help finding the nearest police station?",
            "Would you like contact details of lawyers?"
        ]
    elif intent == "medical":
        suggestions = [
            "Would you like help locating the nearest hospital?",
            "Do you want emergency contact numbers?"
        ]
    else:
        suggestions = [
            "Would you like contact details of nearby lawyers?",
            "Do you want help finding the nearest police station?",
            "Would you like help drafting a complaint?"
        ]

    # Add lawyer suggestion if lawyers are available
    if state.get("lawyers"):
        suggestions.insert(0, "Here are some lawyers you can contact immediately.")

    # Limit to 2–3 suggestions, remove duplicates, preserve order
    seen = set()
    unique_suggestions = []
    for s in suggestions:
        if s not in seen:
            unique_suggestions.append(s)
            seen.add(s)
    state["suggestions"] = unique_suggestions[:3]
    return state
