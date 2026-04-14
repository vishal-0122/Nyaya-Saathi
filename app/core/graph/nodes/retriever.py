from app.mcp.client import call_tool
from langsmith import traceable

@traceable(name="retriever_node", run_type="retriever")
def retriever_node(state: dict):
    query = state.get("rewritten_query") or state.get("query", "")
    query_lower = query.lower()

    fraud_like = any(
        k in query_lower
        for k in [
            "cheated", "cheating", "scam", "fraud", "online fraud", "cyber fraud",
            "phishing", "upi fraud", "bank fraud", "otp"
        ]
    )

    if fraud_like and not any(k in query_lower for k in ["ipc 420", "section 420", "section 406"]):
        query = (
            f"{query}. Relevant Indian law terms: cheating, fraud, online scam, "
            "IPC 420, IPC 406, IPC 66D"
        )

    state["retrieval_query"] = query
    print("Retriever received query:", query)
    result = call_tool(
        "legal_retrieval_tool",
        {"query": query}
    )
    print("MCP RESULT (retriever):", result)
    state["docs"] = result.get("docs", [])
    return state