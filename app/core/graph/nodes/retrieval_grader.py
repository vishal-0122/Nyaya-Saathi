import json
import re

from app.core.llm.openai_client import get_llm
from langsmith import traceable


def _summarize_docs(docs: list) -> str:
    parts = []
    for doc in docs[:3]:
        if isinstance(doc, dict):
            section = doc.get("section") or doc.get("metadata", {}).get("section", "")
            title = doc.get("title") or doc.get("metadata", {}).get("title", "")
            description = doc.get("description") or doc.get("metadata", {}).get("description", "")
            parts.append(
                f"SECTION: {section}\nTITLE: {title}\nDESCRIPTION: {description}"
            )
        else:
            parts.append(str(doc))
    return "\n\n".join(parts)


def _heuristic_grade(query: str, docs: list) -> dict:
    query_lower = (query or "").lower()
    relevant_docs = 0
    scored_docs = []

    for doc in docs:
        text = ""
        if isinstance(doc, dict):
            text = " ".join([
                str(doc.get("section", "")),
                str(doc.get("title", "")),
                str(doc.get("description", "")),
                str(doc.get("category", "")),
            ]).lower()
        else:
            text = str(doc).lower()

        overlap = sum(1 for token in ["ipc", "section", "accident", "injury", "car", "theft", "fraud", "complaint", "fir", "police"] if token in query_lower and token in text)
        if overlap > 0:
            relevant_docs += 1
        scored_docs.append(overlap)

    if not docs:
        return {
            "pass_retrieval": False,
            "retrieval_quality": "low",
            "missing_aspects": ["No documents were retrieved"],
            "notes": "Empty retrieval set."
        }

    if relevant_docs == 0:
        return {
            "pass_retrieval": False,
            "retrieval_quality": "low",
            "missing_aspects": ["Retrieved documents do not appear relevant to the user query"],
            "notes": "Heuristic relevance check failed."
        }

    if relevant_docs < 2:
        return {
            "pass_retrieval": False,
            "retrieval_quality": "medium",
            "missing_aspects": ["Only limited matching legal context was found"],
            "notes": "Some relevance found, but context may be thin."
        }

    return {
        "pass_retrieval": True,
        "retrieval_quality": "high",
        "missing_aspects": [],
        "notes": "Heuristic relevance check passed."
    }


@traceable(name="retrieval_grader_node", run_type="chain")
def retrieval_grader_node(state: dict) -> dict:
    query = state.get("rewritten_query") or state.get("query", "")
    docs = state.get("docs", []) or []

    print("Retrieval grader query:", query)
    print("Retrieval grader docs count:", len(docs))

    grade = None
    llm = get_llm()
    prompt = f"""
You are a retrieval quality grader for a legal RAG system.

Judge whether the retrieved documents are sufficient to answer the user query.
Return ONLY valid JSON with this exact schema:
{{
  "pass_retrieval": true/false,
  "retrieval_quality": "high|medium|low",
  "missing_aspects": ["..."],
  "notes": "short string"
}}

Rules:
- pass_retrieval should be false if the docs are empty, clearly irrelevant, or too weak to support a legal answer.
- Use medium when some relevant context exists but important details are still missing.
- Use high when the retrieved docs clearly match the query.
- Do not add any extra keys.

USER QUERY:
{query}

RETRIEVED DOCS:
{_summarize_docs(docs)}
"""

    try:
        response = llm.invoke(prompt)
        content = getattr(response, "content", str(response)).strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.IGNORECASE | re.DOTALL).strip()
        grade = json.loads(content)
    except Exception:
        grade = _heuristic_grade(query, docs)

    if not isinstance(grade, dict):
        grade = _heuristic_grade(query, docs)

    pass_retrieval = bool(grade.get("pass_retrieval", False))
    retrieval_quality = str(grade.get("retrieval_quality", "low")).lower()
    missing_aspects = grade.get("missing_aspects", [])
    if not isinstance(missing_aspects, list):
        missing_aspects = [str(missing_aspects)]

    state["retrieval_pass"] = pass_retrieval
    state["retrieval_quality"] = retrieval_quality
    state["retrieval_issues"] = missing_aspects
    state["retrieval_grader_notes"] = grade.get("notes", "")
    state["retrieval_grade"] = grade
    print("Retrieval grader result:", grade)
    return state
