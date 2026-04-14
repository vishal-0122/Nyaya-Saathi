from app.mcp.client import call_tool
from langsmith import traceable
import re


def _resolve_draft_query(query: str, conversation_context: str) -> str:
    """Resolve vague draft references against prior conversation context."""
    query = (query or "").strip()
    context_lines = [line.strip() for line in (conversation_context or "").splitlines() if line.strip()]

    if not context_lines:
        return query

    prior_context = context_lines[-1]
    vague_phrases = [
        "this matter",
        "that matter",
        "this incident",
        "that incident",
        "this case",
        "that case",
        "the matter",
        "the incident",
        "same issue",
        "same matter",
        "same incident",
    ]

    is_vague = any(phrase in query.lower() for phrase in vague_phrases)
    asks_for_draft = bool(re.search(r"\b(draft|complaint|fir|application|letter)\b", query, re.IGNORECASE))

    # If vague reference with prior context exists, use the prior context instead
    if (is_vague or asks_for_draft) and prior_context:
        return prior_context

    return query

CATEGORY_MAP = {
    "accident": "Traffic",
    "hit and run": "Traffic",
    "fraud": "Forgery",
    "cyber fraud": "Cyber Crime"
}

@traceable(name="draft_gen_node", run_type="tool")
def draft_gen_node(state: dict):
    query = state.get("query", "")
    conversation_context = (state.get("conversation_context") or "").strip()

    draft_query = _resolve_draft_query(query, conversation_context)

    result = call_tool(
        "draft_generator_tool",
        {"query": draft_query}
    )

    state["draft"] = result.get("draft", "")
    state["draft_category"] = result.get("category", "")

    return state