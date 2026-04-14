import requests
import os

MCP_URL = os.getenv("MCP_URL", "http://127.0.0.1:8001/mcp")
MCP_FALLBACK_URLS = [
    MCP_URL,
    "http://mcp:8001/mcp",
    "http://host.docker.internal:8001/mcp",
    "http://127.0.0.1:8001/mcp",
]

TOOL_TIMEOUTS = {
    "legal_retrieval_tool": 20,
    "case_search_tool": 15,
    "lawyer_lookup_tool": 10,
    "draft_generator_tool": 10,
    "emergency_services_tool": 6,
}

def call_tool(tool_name: str, payload: dict) -> dict:
    last_error = None
    seen = set()
    timeout_seconds = TOOL_TIMEOUTS.get(tool_name, 10)

    for url in MCP_FALLBACK_URLS:
        if not url or url in seen:
            continue
        seen.add(url)
        try:
            response = requests.post(
                url,
                json={
                    "method": tool_name,
                    "params": payload
                },
                timeout=timeout_seconds
            )

            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                raise Exception(data.get("message", "Tool failed"))

            return data.get("result", {})

        except Exception as e:
            last_error = e
            print(f"[MCP ERROR] url={url} error={e}")

    return {"_mcp_error": str(last_error) if last_error else "Unknown MCP error"}