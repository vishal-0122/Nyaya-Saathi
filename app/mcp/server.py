import logging
from unittest import result
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from fastapi import FastAPI, Request, Body
from fastapi.responses import JSONResponse

# Import your existing logic
from app.core.graph.builder import build_graph
from app.services.legal_service import retrieve_legal_docs
from app.services.case_service import search_cases
from app.services.lawyer_service import find_lawyers
from app.services.draft_service import generate_draft
from app.mcp.tools.emergency_services import emergency_services_tool

# from app.core.graph.nodes.retriever import retriever_node
# from app.core.graph.nodes.case_node import case_node
# from app.core.graph.nodes.lawyer_node import lawyer_node
# from app.mcp.tools.draft_generator import generate_complaint_draft
# from app.core.graph.nodes.reasoning import reasoning_node

# -----------------------------
# App & Logger Setup
# -----------------------------
graph = build_graph()  # Build the graph once at startup
app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

# query = payload.get("query", "")
# print("Incoming API query:", query)

# -----------------------------
# Tool Registry with Metadata
# -----------------------------
tool_registry = {}

def register_tool(name: str, description: str):
    def decorator(func):
        tool_registry[name] = {
            "func": func,
            "description": description
        }
        return func
    return decorator

# -----------------------------
# Tool Definitions
# -----------------------------

@register_tool(
    "legal_retrieval_tool",
    "Retrieve relevant legal documents based on user query"
)
def legal_retrieval_tool(query: str):
    docs = retrieve_legal_docs(query)
    return {"docs": docs}


@register_tool(
    "case_search_tool",
    "Fetch recent similar legal cases based on user query"
)
def case_search_tool(query: str):
    cases = search_cases(query)
    return {"cases": cases}


@register_tool(
    "lawyer_lookup_tool",
    "Retrieve lawyers based on user location"
)
def lawyer_lookup_tool(query: str):
    lawyers = find_lawyers(query)
    return {"lawyers": lawyers}


@register_tool(
    "draft_generator_tool",
    "Generate complaint or FIR draft based on user incident"
)
def draft_generator_tool(query: str):
    result = generate_draft(query)
    return result

@register_tool(
    "emergency_services_tool",
    "Find nearby emergency services (police or hospital) for a given location."
)
def emergency_services_tool_mcp(location: str, service_type: str):
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(emergency_services_tool, location, service_type)
        try:
            services = future.result(timeout=4)
        except TimeoutError:
            services = [
                {
                    "name": f"No live {service_type} results found",
                    "address": f"Emergency lookup timed out for {location}. Please try again in a moment.",
                    "source": "fallback",
                }
            ]
        except Exception:
            services = [
                {
                    "name": f"No live {service_type} results found",
                    "address": f"Emergency lookup failed for {location}. Please try again in a moment.",
                    "source": "fallback",
                }
            ]
    return {"emergency_services": services}


@app.post("/query")
async def query_endpoint(payload: dict = Body(...)):
    query = payload.get("query", "")
    state = {
        "query": query,
        "session_id": payload.get("session_id", ""),
    }
    result = graph.invoke(state)
    return {
        "status": "success",
        "result": result.get("answer", result)
    }

# -----------------------------
# MCP Endpoint
# -----------------------------

@app.post("/mcp")
async def mcp_server(request: Request):
    try:
        data = await request.json()
        method = data.get("method")
        params = data.get("params", {})

        logger.info(f"Tool called: {method} | Params: {params}")

        tool_entry = tool_registry.get(method)

        if not tool_entry:
            return JSONResponse(
                {
                    "status": "error",
                    "message": f"Unknown method: {method}"
                },
                status_code=400
            )

        result = tool_entry["func"](**params)

        return JSONResponse({
            "status": "success",
            "tool": method,
            "result": result
        })

    except Exception as e:
        logger.exception("Error during MCP execution")
        return JSONResponse(
            {
                "status": "error",
                "message": str(e)
            },
            status_code=500
        )

# -----------------------------
# Health Check
# -----------------------------

@app.get("/health")
def health():
    return {"status": "MCP server running"}

# -----------------------------
# List Available Tools
# -----------------------------

@app.get("/tools")
def list_tools():
    return {
        "tools": [
            {
                "name": name,
                "description": tool_registry[name]["description"]
            }
            for name in tool_registry
        ]
    }