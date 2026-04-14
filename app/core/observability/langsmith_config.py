import logging
import os
from typing import Dict, Any

import langsmith
from langsmith import Client

logger = logging.getLogger(__name__)
_startup_check_warned = False


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def configure_langsmith() -> None:
    """Enable LangSmith tracing when API key is present."""
    global _startup_check_warned

    # Ensure Python uses OS trust store (important on some Windows setups).
    try:
        import truststore

        truststore.inject_into_ssl()
    except Exception:
        # Soft-fail: tracing may still work depending on local cert setup.
        pass

    api_key = os.getenv("LANGSMITH_API_KEY", "").strip()

    if not api_key:
        logger.info("LangSmith tracing disabled: LANGSMITH_API_KEY not set")
        return

    # Keep both flags for compatibility with LangChain/LangGraph tracing stacks.
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    os.environ.setdefault("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    os.environ.setdefault("LANGSMITH_PROJECT", "nyaya-saathi")
    os.environ.setdefault("LANGCHAIN_PROJECT", "nyaya-saathi")

    # Mirror credentials into both env families because different LangChain/LangSmith
    # versions consult different variable names.
    os.environ["LANGSMITH_API_KEY"] = api_key
    os.environ["LANGCHAIN_API_KEY"] = api_key

    project = os.getenv("LANGSMITH_PROJECT", "nyaya-saathi").strip().strip('"').strip("'")
    os.environ["LANGSMITH_PROJECT"] = project
    os.environ["LANGCHAIN_PROJECT"] = project

    insecure_skip_verify = _env_bool("LANGSMITH_INSECURE_SKIP_VERIFY", False)

    session = None
    if insecure_skip_verify:
        import requests
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        session = requests.Session()
        session.verify = False

    workspace_id = os.getenv("LANGSMITH_WORKSPACE_ID", "").strip() or None

    client = Client(
        api_key=api_key,
        api_url=os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"),
        session=session,
        workspace_id=workspace_id,
    )

    # Force all traceable decorators/wrappers to use this exact client.
    langsmith.configure(
        client=client,
        enabled=True,
        project_name=project,
        tags=["nyaya-saathi"],
    )

    check_on_startup = _env_bool("LANGSMITH_STARTUP_CHECK", False)
    if not check_on_startup:
        logger.info(
            "LangSmith tracing enabled (project=%s, startup_check=disabled, insecure_skip_verify=%s)",
            project,
            str(insecure_skip_verify).lower(),
        )
        return

    try:
        # This call validates credentials/connectivity at startup.
        _ = client.list_projects(limit=1)
        logger.info(
            "LangSmith tracing enabled (project=%s, insecure_skip_verify=%s)",
            project,
            str(insecure_skip_verify).lower(),
        )
    except Exception as exc:
        if not _startup_check_warned:
            logger.warning(
                "LangSmith tracing is enabled, but startup connectivity check failed once (%s). "
                "Tracing will continue in soft-fail mode.",
                exc.__class__.__name__,
            )
            _startup_check_warned = True


def is_langsmith_enabled() -> bool:
    return (
        os.getenv("LANGSMITH_TRACING", "").strip().lower() == "true"
        and bool(os.getenv("LANGSMITH_API_KEY", "").strip())
    )


def build_langsmith_run_config(
    *,
    run_name: str,
    session_id: str,
    response_format: str,
    query: str,
    route: str,
) -> Dict[str, Any]:
    """Construct a consistent LangSmith run config for LangGraph invocation."""
    return {
        "run_name": run_name,
        "tags": ["nyaya-saathi", "api", route, "langgraph"],
        "metadata": {
            "session_id": session_id,
            "response_format": response_format,
            "query_length": len(query or ""),
            "has_question_mark": "?" in (query or ""),
            "project": os.getenv("LANGSMITH_PROJECT", "nyaya-saathi"),
        },
    }
