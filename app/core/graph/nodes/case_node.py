from app.mcp.client import call_tool
from langsmith import traceable

@traceable(name="case_node", run_type="tool")
def case_node(state: dict):
    query = state.get("rewritten_query") or state.get("query", "")
    print("Case node query:", query)
    result = call_tool(
        "case_search_tool",
        {"query": query}
    )
    print("MCP RESULT (case_node):", result)
    state["cases"] = result.get("cases", [])
    return state