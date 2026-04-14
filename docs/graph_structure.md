# LangGraph Structure

This document maps the current graph defined in [app/core/graph/builder.py](../app/core/graph/builder.py).

## Overview

```text
                                   +------------------+
                                   |      START       |
                                   +------------------+
                                            |
                                            v
                                   +------------------+
                                   |     planner      |
                                   +------------------+
                  +-------------------+------------+-------------------+----------------------+
                  |                   |            |                   |                      |
                  |                   |            |                   |                      |
                  v                   v            v                   v                      v
        +------------------+  +----------------+  +----------------+  +-------------------+  +-------------------+
        | general_query    |  | use_emergency   |  | lawyer_lookup  |  | draft_generator   |  | default legal flow|
        | -> reasoning     |  | -> emergency    |  | -> lawyer_node |  | -> draft_generator|  | -> retriever      |
        +------------------+  +----------------+  +----------------+  +-------------------+  +-------------------+

                              Direct branches:

    emergency       -------------------------------> reasoning
    lawyer_node     -------------------------------> reasoning
    draft_generator -------------------------------> reasoning

                              Advanced RAG branch (legal queries only):

    retriever -> retrieval_grader

    retrieval_grader
        |
        +--> if pass_retrieval = false AND attempt < max_attempts
        |         -> query_rewriter -> retriever
        |
        +--> if use_case_search = true -> case_node -> reasoning
        |
        +--> otherwise -> reasoning

                              Final composition path:

    reasoning -> suggestion -> safety -> FINISH
```

## Node Roles

- `planner`: Classifies the query and decides the first route.
- `retriever`: Calls the legal retrieval tool for legal queries. This is where the advanced RAG loop begins.
- `retrieval_grader`: Evaluates retrieved documents and decides whether retrieval is good enough.
- `query_rewriter`: Rewrites weak queries for a second retrieval pass.
- `case_node`: Fetches supporting legal case/news results.
- `lawyer_node`: Fetches lawyer results directly. It does not use the advanced RAG loop.
- `emergency`: Fetches emergency service information.
- `draft_generator`: Generates complaint/FIR drafts directly.
- `reasoning`: Produces the final structured answer from the gathered context.
- `suggestion`: Adds follow-up suggestions.
- `safety`: Applies the final disclaimer policy and ends the graph.

## Conditional Edges

### From `planner`
- `general_query` -> `reasoning`
- `use_emergency = true` -> `emergency`
- `intent = lawyer_lookup` -> `lawyer_node`
- `intent = draft_generator` or draft flags -> `draft_generator`
- otherwise -> `retriever`

### From `retriever`
- always -> `retrieval_grader`

### From `retrieval_grader`
- `pass_retrieval = false` and `attempt < max_attempts` -> `query_rewriter`
- `use_case_search = true` -> `case_node`
- otherwise -> `reasoning`

### From `query_rewriter`
- always -> `retriever`

### Important clarification
- The advanced RAG loop is only on the legal retrieval path: `retriever -> retrieval_grader -> query_rewriter -> retriever`.
- `lawyer_node` is a direct lookup branch and does not go through the RAG loop.
- `draft_generator` is also a direct branch and does not go through the RAG loop.

## Fixed Edges

- `emergency` -> `reasoning`
- `case_node` -> `reasoning`
- `lawyer_node` -> `reasoning`
- `draft_generator` -> `reasoning`
- `reasoning` -> `suggestion`
- `suggestion` -> `safety`

## Notes

- The graph entry point is `planner`.
- The graph finish point is `safety`.
- The retrieval loop is a corrective pass: `retriever -> retrieval_grader -> query_rewriter -> retriever`.
- `reasoning` is intentionally kept as the final answer composer and is not responsible for tool calls.
