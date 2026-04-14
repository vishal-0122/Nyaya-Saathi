from app.mcp.client import call_tool
from langsmith import traceable


@traceable(name="lawyer_node", run_type="tool")
def lawyer_node(state: dict):
    query = state.get("query", "")

    result = call_tool("lawyer_lookup_tool", {"query": query})

    state["lawyers"] = result.get("lawyers", [])
    return state
