import json
import re

from app.core.llm.openai_client import get_llm
from langsmith import traceable


def _fallback_rewrite(query: str, issues: list) -> str:
    query = (query or "").strip()
    issue_text = " ".join(str(item) for item in issues if item)
    if not query:
        return "legal complaint India IPC"

    additions = []
    lowered = query.lower()
    if "accident" in lowered or "hit by a car" in lowered or "hit and run" in lowered:
        additions.append("Indian legal provisions for road accident and injury")
    if "theft" in lowered or "property" in lowered:
        additions.append("relevant IPC sections for theft and property offences")
    if "fraud" in lowered or "cyber" in lowered:
        additions.append("relevant Indian legal provisions for fraud or cybercrime")
    if issue_text:
        additions.append(issue_text)

    suffix = "; ".join(additions)
    if suffix:
        return f"{query} | legal context: {suffix}"
    return f"{query} | Indian legal context and IPC sections"


@traceable(name="query_rewriter_node", run_type="chain")
def query_rewriter_node(state: dict) -> dict:
    query = state.get("rewritten_query") or state.get("query", "")
    issues = state.get("retrieval_issues", []) or []
    attempt = int(state.get("retrieval_attempt", 0)) + 1
    max_attempts = int(state.get("retrieval_max_attempts", 2))

    print("Query rewriter attempt:", attempt, "of", max_attempts)
    print("Query rewriter original query:", query)
    print("Query rewriter issues:", issues)

    llm = get_llm()
    prompt = f"""
You rewrite user legal queries for a second retrieval pass.

Return ONLY a single rewritten query string. No markdown, no bullets, no explanation.

Rules:
- Preserve the user's original facts and intent.
- Do not invent events, people, places, or dates.
- Improve retrieval by adding legal context terms.
- Keep it concise.
- Prefer Indian legal framing when appropriate.

ORIGINAL QUERY:
{query}

RETRIEVAL ISSUES:
{json.dumps(issues)}
"""

    rewritten = ""
    try:
        response = llm.invoke(prompt)
        rewritten = getattr(response, "content", str(response)).strip()
        rewritten = re.sub(r"^```(?:text)?\s*|\s*```$", "", rewritten, flags=re.IGNORECASE | re.DOTALL).strip()
    except Exception:
        rewritten = ""

    if not rewritten:
        rewritten = _fallback_rewrite(query, issues)

    state["retrieval_attempt"] = attempt
    state["rewritten_query"] = rewritten
    history = state.get("rewrite_history", [])
    if not isinstance(history, list):
        history = [str(history)]
    history.append({"attempt": attempt, "query": rewritten})
    state["rewrite_history"] = history
    state["retrieval_continue"] = attempt < max_attempts
    print("Query rewriter output:", rewritten)
    return state
