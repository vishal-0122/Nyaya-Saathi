# Nyaya Saathi: Your Legal AI Consultant

[![CI/CD Pipeline](https://github.com/vishal-0122/Nyaya-Saathi/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/vishal-0122/Nyaya-Saathi/actions/workflows/ci-cd.yml)
[![Docker Image](https://img.shields.io/docker/pulls/vishal0122/nyaya-saathi-app?label=Docker%20Image&logo=docker)](https://hub.docker.com/r/vishal0122/nyaya-saathi-app)

## Overview

Nyaya Saathi is an **AI-powered legal assistance system** designed to help users understand their legal situations and take the right next steps.

Instead of navigating complex legal documents or fragmented information sources, users can describe their situation in natural language and receive:

- a clear explanation of what may apply legally,
- actionable next steps,
- relevant laws and case context,
- and guidance on who to contact (lawyers, police, emergency services).

The system acts as a **first-response legal assistant**, focused on clarity, speed, and practical usefulness rather than legal jargon.

---

## What Makes It Different

Nyaya Saathi is not just a chatbot — it is a **structured, agent-driven system** that combines reasoning, retrieval, and real-world tool integration.

It is designed to:

- understand user intent from unstructured input,
- retrieve relevant legal context using advanced RAG pipelines,
- generate structured, actionable responses,
- integrate external tools (lawyers, emergency services, complaint drafting),
- and maintain conversation context across sessions.

---

## Business Problem

Accessing legal help at the first point of interaction is often inefficient and inconsistent.

Key challenges include:

- Users describe problems in everyday language, not legal terminology  
- Legal information is scattered and difficult to interpret quickly  
- Initial guidance varies significantly across platforms  
- Support teams repeatedly handle the same first-level queries  
- In urgent situations, users often don’t know what to do next  

---

## Solution

Nyaya Saathi addresses this gap by providing a structured AI-driven legal assistance pipeline that can:

- classify user intent in real time  
- retrieve and validate relevant legal information  
- provide clear, step-by-step actionable guidance  
- generate complaint drafts when needed  
- connect users to lawyers and emergency services  
- retain conversational context for continuity  

This results in:

- faster and more consistent first-level legal guidance  
- reduced operational overhead for support systems  
- improved accessibility to legal awareness for everyday users  

---

## Technical Highlights

The platform is built using a modular, production-ready architecture:

- LangGraph-based multi-agent orchestration  
- Advanced RAG pipeline with grading and query rewriting  
- MCP-based tool execution layer  
- Chroma vector database for retrieval  
- Supabase PostgreSQL as a production-oriented memory database for persistent session and conversation context  
- LangSmith for observability and debugging  
- Dockerized deployment with CI/CD via GitHub Actions  

---

## Live Demo

- App URL: [Click Here](http://15.206.119.175:8501/)

## Product Preview

<img width="1917" height="1031" alt="Image" src="https://github.com/user-attachments/assets/ded72073-1054-4219-9e77-0884d9d2756b" />

## Graph Architecture

<img width="1286" height="762" alt="Image" src="https://github.com/user-attachments/assets/b9567300-dc03-4ca3-80e5-c8549562c910" />

## Key Features

- Multi-agent legal routing by intent
- Advanced RAG loop with retrieval quality control
- Human-in-the-Loop (HITL) checkpoints are currently implemented in case search and query rewriting, with additional HITL pathways under active design for other high-impact nodes/tools.
- Legal retrieval + case search + lawyer lookup + emergency guidance + draft generation
- Persistent chat sessions and history
- LangSmith-based LLMOps and traceability
- Dockerized local and cloud deployment

---

## Repository Structure

```text
NyayaSaathi/
├── README.md
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .dockerignore
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── app/
│   ├── main.py
│   ├── api/
│   │   └── routes/
│   │       └── query.py
│   ├── core/
│   │   ├── graph/
│   │   │   ├── builder.py
│   │   │   ├── state.py
│   │   │   └── nodes/
│   │   │       ├── planner.py
│   │   │       ├── retriever.py
│   │   │       ├── retrieval_grader.py
│   │   │       ├── query_rewriter.py
│   │   │       ├── case_node.py
│   │   │       ├── lawyer_node.py
│   │   │       ├── emergency_node.py
│   │   │       ├── draft_gen_node.py
│   │   │       ├── reasoning.py
│   │   │       ├── suggestion.py
│   │   │       └── safety.py
│   │   ├── rag/
│   │   │   └── embedding.py
│   │   ├── llm/
│   │   │   └── openai_client.py
│   │   └── observability/
│   │       └── langsmith_config.py
│   ├── db/
│   │   ├── chroma/
│   │   │   └── client.py
│   │   └── postgres/
│   │       ├── connection.py
│   │       ├── init_db.py
│   │       ├── models.py
│   │       └── queries.py
│   ├── mcp/
│   │   ├── client.py
│   │   ├── server.py
│   │   └── tools/
│   │       ├── case_search.py
│   │       ├── lawyer_lookup.py
│   │       ├── draft_generator.py
│   │       └── emergency_services.py
│   ├── models/
│   │   ├── request.py
│   │   └── response.py
│   ├── services/
│   │   ├── legal_service.py
│   │   ├── case_service.py
│   │   ├── lawyer_service.py
│   │   └── draft_service.py
│   └── utils/
│       └── prompts.py
├── config/
│   └── settings.py
├── frontend/
│   └── app.py
├── scripts/
│   ├── ingest_data.py
│   ├── ingest_dummy_data.py
│   ├── check_chroma.py
│   └── seed_lawyers.py
└── data/
    └── raw/
        └── legal_data.json
```

---

## File Walkthrough

## 1) Application Entry Points

- `app/main.py`
  - Main FastAPI app bootstrap.
- `frontend/app.py`
  - Streamlit frontend entrypoint.
- `app/mcp/server.py`
  - MCP server runtime that exposes tool methods.
- `app/mcp/client.py`
  - MCP client used by graph nodes to call tools.

## 2) API Layer

- `app/api/routes/query.py`
  - Main query endpoint.
  - Session listing endpoint.
  - History retrieval/deletion endpoints.
  - Graph invocation and response shaping.

## 3) Graph Orchestration Core

- `app/core/graph/builder.py`
  - Builds LangGraph nodes + edges.
  - Defines route flow.
- `app/core/graph/state.py`
  - Shared graph state schema.

## 4) Graph Node Responsibilities

- `app/core/graph/nodes/planner.py`: intent routing decision.
- `app/core/graph/nodes/retriever.py`: legal retrieval branch entry.
- `app/core/graph/nodes/case_node.py`: supporting case references.
- `app/core/graph/nodes/lawyer_node.py`: lawyer lookup branch.
- `app/core/graph/nodes/emergency_node.py`: emergency branch.
- `app/core/graph/nodes/draft_gen_node.py`: draft generation branch.
- `app/core/graph/nodes/reasoning.py`: final answer composition.
- `app/core/graph/nodes/suggestion.py`: follow-up suggestions.
- `app/core/graph/nodes/safety.py`: disclaimer/safety finalization.

## 5) Advanced RAG (Dedicated)

The advanced RAG logic is primarily controlled by the following files:

- `app/core/graph/nodes/retrieval_grader.py`
  - Scores retrieved context quality.
  - Checks whether retrieved context is sufficient.
  - Decides if the query should be rewritten.

- `app/core/graph/nodes/query_rewriter.py`
  - Rewrites weak or ambiguous legal queries.
  - Produces improved retrieval queries.
  - Feeds query back into retriever for another pass.

- `app/core/graph/nodes/retriever.py`
  - Calls legal retrieval via MCP and updates graph state.

- `app/core/rag/embedding.py`
  - Generates embedding vectors through Ollama endpoint(s).

Advanced RAG loop:

```text
retriever -> retrieval_grader -> query_rewriter -> retriever
```

## 6) LLM + Observability

- `app/core/llm/openai_client.py`
  - OpenAI interaction helper.
- `app/core/observability/langsmith_config.py`
  - LangSmith configuration and tracing support.

## 7) MCP Tool Implementations

- `app/mcp/tools/case_search.py`
- `app/mcp/tools/lawyer_lookup.py`
- `app/mcp/tools/draft_generator.py`
- `app/mcp/tools/emergency_services.py`

These tools are invoked through MCP to keep graph logic modular.

## 8) Business Services

- `app/services/legal_service.py`
- `app/services/case_service.py`
- `app/services/lawyer_service.py`
- `app/services/draft_service.py`

These services hold domain logic used by nodes/tools.

## 9) Persistence Layer

- `app/db/chroma/client.py`
  - Chroma client and collection access.
- `app/db/postgres/connection.py`
  - SQLAlchemy engine/session setup.
- `app/db/postgres/models.py`
  - DB models.
- `app/db/postgres/queries.py`
  - DB query helpers.
- `app/db/postgres/init_db.py`
  - DB init helper script.

## 10) Models, Config, Prompts

- `app/models/request.py`
- `app/models/response.py`
- `config/settings.py`
- `app/utils/prompts.py`

## 11) Data Ops Scripts

- `scripts/ingest_data.py`
- `scripts/ingest_dummy_data.py`
- `scripts/check_chroma.py`
- `scripts/seed_lawyers.py`

---

## Technology Stack

### Core Runtime

- FastAPI
- Streamlit
- LangGraph
- Pydantic
- SQLAlchemy

### AI / Retrieval

- OpenAI
- Ollama (embedding runtime)
- Chroma DB (vector retrieval)
- Supabase PostgreSQL (persistent memory)

### Tooling / LLMOps

- MCP (Model Context Protocol)
- LangSmith

### DevOps / Deployment

- Docker
- Docker Compose
- Docker Hub
- GitHub Actions CI/CD
- AWS EC2

---

## Deployment Model

- Local: Docker Compose
- CI: image build validation on PR
- CD: Docker Hub publish on main/tags/manual workflow
- Cloud: EC2 pulls image from Docker Hub and runs Compose stack

---

## Environment Variables

```dotenv
OPENAI_API_KEY=your_openai_key
DATABASE_URL=your_supabase_direct_url
DATABASE_URL_DOCKER=your_supabase_pooler_url
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_TRACING=true
LANGCHAIN_TRACING_V2=true
LANGSMITH_PROJECT=nyaya-saathi
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_WORKSPACE_ID=
LANGSMITH_INSECURE_SKIP_VERIFY=true
LANGSMITH_STARTUP_CHECK=false
```

---

## Author

**Vishal Dangiwala**

GitHub: [@vishal-0122](https://github.com/vishal-0122)

---

## Summary

Nyaya Saathi bridges the gap between **legal complexity and everyday understanding** by combining AI reasoning with real-world utility, making legal assistance more accessible, structured, and actionable.

---

## ⚠️ Disclaimer

Nyaya Saathi is intended for informational assistance and legal workflow support. It does not replace advice from a qualified lawyer.

---


