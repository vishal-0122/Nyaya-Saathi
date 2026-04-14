# langgraph imports
from langgraph.graph import StateGraph

# nodes
from app.core.graph.nodes.planner import planner_node
from app.core.graph.nodes.retriever import retriever_node
from app.core.graph.nodes.case_node import case_node
from app.core.graph.nodes.lawyer_node import lawyer_node
from app.core.graph.nodes.emergency_node import emergency_node
from app.core.graph.nodes.reasoning import reasoning_node
from app.core.graph.nodes.retrieval_grader import retrieval_grader_node
from app.core.graph.nodes.query_rewriter import query_rewriter_node
from app.core.graph.nodes.suggestion import suggestion_node
from app.core.graph.nodes.safety import safety_node
from app.core.graph.nodes.draft_gen_node import draft_gen_node


def build_graph():
    graph = StateGraph(dict)

    # ------------------ ADD NODES ------------------
    graph.add_node("planner", planner_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("case_node", case_node)
    graph.add_node("lawyer_node", lawyer_node)
    graph.add_node("emergency", emergency_node)
    graph.add_node("draft_generator", draft_gen_node)
    graph.add_node("retrieval_grader", retrieval_grader_node)
    graph.add_node("query_rewriter", query_rewriter_node)
    graph.add_node("reasoning", reasoning_node)
    graph.add_node("suggestion", suggestion_node)
    graph.add_node("safety", safety_node)

    # ------------------ ROUTING LOGIC ------------------

    def planner_route(state):
        plan = state.get("plan", {})
        print("PLAN:", state.get("plan"))
        print("INTENT:", state.get("intent"))

        if state.get("intent") == "general_query":
            return "reasoning"

        # 🚨 FIRST PRIORITY: EMERGENCY
        if state.get("intent") == "emergency" or plan.get("use_emergency"):
            return "emergency"

        # Lawyer direct
        if state.get("intent") == "lawyer_lookup":
            return "lawyer_node"

        # Draft generator (robust)
        if state.get("intent") == "draft_generator" or plan.get("use_draft_generator") or plan.get("generate_draft"):
            return "draft_generator"

        # Otherwise normal flow
        return "retriever"

    def retriever_route(state):
        print("Retriever route:", state.get("plan"))
        return "retrieval_grader"

    def retrieval_grader_route(state):
        plan = state.get("plan", {})
        pass_retrieval = bool(state.get("retrieval_pass", False))
        attempt = int(state.get("retrieval_attempt", 0))
        max_attempts = int(state.get("retrieval_max_attempts", 2))

        if not pass_retrieval and attempt < max_attempts:
            return "query_rewriter"

        if plan.get("use_case_search"):
            return "case_node"

        return "reasoning"

    def query_rewriter_route(state):
        return "retriever"

    # ------------------ ADD EDGES ------------------

    graph.add_conditional_edges(
        "planner",
        planner_route,
        {
            "emergency": "emergency",
            "lawyer_node": "lawyer_node",
            "draft_generator": "draft_generator",
            "reasoning": "reasoning",
            "retriever": "retriever"
        }
    )

    graph.add_conditional_edges(
        "retriever",
        retriever_route,
        {
            "retrieval_grader": "retrieval_grader",
            "reasoning": "reasoning"
        }
    )

    graph.add_conditional_edges(
        "retrieval_grader",
        retrieval_grader_route,
        {
            "query_rewriter": "query_rewriter",
            "case_node": "case_node",
            "reasoning": "reasoning"
        }
    )

    graph.add_conditional_edges(
        "query_rewriter",
        query_rewriter_route,
        {
            "retriever": "retriever"
        }
    )


    # Tool outputs → reasoning
    graph.add_edge("emergency", "reasoning")
    graph.add_edge("case_node", "reasoning")
    graph.add_edge("lawyer_node", "reasoning")
    graph.add_edge("draft_generator", "reasoning")

    # Final pipeline
    graph.add_edge("reasoning", "suggestion")
    graph.add_edge("suggestion", "safety")

    graph.set_entry_point("planner")
    graph.set_finish_point("safety")

    return graph.compile()