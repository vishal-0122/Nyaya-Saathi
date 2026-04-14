import streamlit as st
import requests
import json
import ast
import re
import time
import os
from datetime import datetime
from typing import Optional, List, Dict, Iterator
import uuid

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
QUERY_ENDPOINT = f"{BACKEND_URL}/query"
SESSIONS_ENDPOINT = f"{BACKEND_URL}/sessions"
HISTORY_ENDPOINT = f"{BACKEND_URL}/history"
QUERY_TIMEOUT_SECONDS = 90
SESSIONS_TIMEOUT_SECONDS = 5

# Page configuration
st.set_page_config(
    page_title="NYAYA SAATHI - Your Legal AI Consultant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    :root {
        --primary: #0f766e;
        --primary-light: #14b8a6;
        --accent: #b45309;
        --bg-main: #f8fafc;
        --bg-card: #ffffff;
        --bg-sidebar: #0f172a;
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --border: #e2e8f0;
    }
    html, body {
        background: var(--bg-main) !important;
        color: var(--text-primary) !important;
    }
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    .main,
    .block-container {
        background: var(--bg-main) !important;
        color: var(--text-primary) !important;
        font-family: "Inter", "Segoe UI", sans-serif;
    }
    [data-testid="stHeader"],
    [data-testid="stToolbar"] {
        background: transparent;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    [data-testid="stSidebar"] * {
        color: #f8fafc;
    }
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #f8fafc;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255, 255, 255, 0.12);
        border-color: rgba(255, 255, 255, 0.22);
        transform: translateX(1px);
    }
    [data-testid="stSidebar"] .stButton > button:focus-visible {
        outline: 2px solid rgba(20, 184, 166, 0.75);
        outline-offset: 2px;
    }
    .block-container {
        padding-top: 1.2rem;
        max-width: 1180px;
    }
    .hero-shell {
        background: #6d7278;
        color: #0f172a;
        border-radius: 18px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #e2e8f0;
    }
    .hero-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
    }
    .hero-subtitle {
        font-size: 1rem;
        margin-top: 0.3rem;
        color: #334155;
    }
    .hero-copy {
        margin-top: 0.6rem;
        color: #475569;
        line-height: 1.6;
    }
    /* ===== CHAT MESSAGE CONTAINER ===== */
    [data-testid="stChatMessage"] {
        background: #ffffff !important;
        border: 1px solid var(--border) !important;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.05) !important;
        border-radius: 14px !important;
        padding: 12px 14px !important;
        margin: 0.75rem 0 !important;
    }
    [data-testid="stChatMessage"] .stMarkdown,
    [data-testid="stChatMessage"] .stMarkdown p,
    [data-testid="stChatMessage"] .stMarkdown li,
    [data-testid="stChatMessage"] .stMarkdown span,
    [data-testid="stChatMessage"] .stMarkdown div,
    [data-testid="stChatMessage"] h1,
    [data-testid="stChatMessage"] h2,
    [data-testid="stChatMessage"] h3,
    [data-testid="stChatMessage"] h4,
    [data-testid="stChatMessage"] h5,
    [data-testid="stChatMessage"] h6,
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] div {
        color: #0f172a !important;
        opacity: 1 !important;
    }
    [data-testid="stChatMessage"] a {
        color: var(--primary) !important;
    }

    /* ===== USER MESSAGE BUBBLE ===== */
    .user-bubble {
        background: #2563eb;
        color: white;
        padding: 10px 14px;
        border-radius: 14px;
        max-width: 75%;
        margin-left: auto;
        margin-right: 0;
        font-size: 0.95rem;
        line-height: 1.5;
        word-wrap: break-word;
        white-space: pre-wrap;
    }

    .user-bubble p,
    .user-bubble span,
    .user-bubble div,
    .user-bubble li,
    .user-bubble [data-testid="stMarkdownContainer"] {
        color: white !important;
    }

    .user-bubble a {
        color: #93c5fd !important;
        text-decoration: underline;
    }

    /* ===== ASSISTANT MESSAGE BUBBLE ===== */
    .assistant-bubble {
        background: #ffffff;
        color: #0f172a;
        padding: 12px 14px;
        border-radius: 14px;
        max-width: 75%;
        margin-left: 0;
        margin-right: auto;
        border: 1px solid #e2e8f0;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.05);
        font-size: 0.95rem;
        line-height: 1.6;
        word-wrap: break-word;
        white-space: pre-wrap;
    }

    .assistant-bubble p,
    .assistant-bubble span,
    .assistant-bubble div,
    .assistant-bubble li,
    .assistant-bubble [data-testid="stMarkdownContainer"] {
        color: #0f172a !important;
    }

    .assistant-bubble a {
        color: var(--primary) !important;
        text-decoration: underline;
    }
    .stTextInput input {
        border-radius: 999px !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        background: #ffffff !important;
        border: 1px solid var(--border) !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.06);
        color: var(--text-primary) !important;
        caret-color: #0f172a !important;
    }
    .stTextInput input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.12) !important;
    }
    .stButton > button,
    .stFormSubmitButton > button {
        border-radius: 999px;
        border: none;
        background: var(--primary) !important;
        color: white !important;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 4px 10px rgba(15, 23, 42, 0.08);
    }
    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        background: var(--primary-light) !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 14px rgba(0, 0, 0, 0.1);
    }
    .response-card {
        background-color: #ffffff;
        border: 1px solid var(--border);
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.8rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
    }
    .law-section {
        background-color: #ffffff;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 0.75rem;
        border: 1px solid var(--border);
        border-left: 3px solid var(--accent);
    }
    .case-section {
        background-color: #ffffff;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 0.75rem;
        border: 1px solid var(--border);
        border-left: 3px solid #7c3aed;
    }
    .footer-shell {
        background: #ffffff;
        border: 1px solid var(--border);
        border-radius: 1rem;
        padding: 0.9rem 1rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
    }
    .main div[data-testid="stHorizontalBlock"] {
        position: sticky;
        bottom: 0;
        z-index: 30;
        background: linear-gradient(180deg, rgba(248, 250, 252, 0.2) 0%, rgba(248, 250, 252, 0.96) 18%, rgba(248, 250, 252, 1) 100%);
        padding: 0.85rem 0 1rem;
        margin-top: 0.25rem;
        border-top: 1px solid rgba(226, 232, 240, 0.9);
        box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.05);
        backdrop-filter: blur(10px);
    }
    .main div[data-testid="stHorizontalBlock"] .stTextInput input {
        min-height: 52px;
    }
    .main div[data-testid="stHorizontalBlock"] .stButton > button {
        min-height: 52px;
    }
    .stTextInput > div > div > input,
    .stTextInput input::placeholder {
        color: var(--text-primary) !important;
        opacity: 1 !important;
    }
    .stMarkdown,
    .stMarkdown p,
    .stMarkdown li,
    .stMarkdown span,
    .stMarkdown div {
        color: var(--text-primary) !important;
    }
    .stMarkdown p,
    .stMarkdown li {
        line-height: 1.6;
    }
    .stCaption {
        color: var(--text-secondary) !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px;
    }
    [data-testid="column"] .stButton > button {
        width: 100%;
    }
    .stSidebar [data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.03);
    }
    .stSidebar .stMarkdown,
    .stSidebar .stMarkdown p,
    .stSidebar .stMarkdown li,
    .stSidebar .stMarkdown span,
    .stSidebar .stMarkdown div {
        color: #f8fafc !important;
    }
    </style>
    """, unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "conversation" not in st.session_state:
        st.session_state.conversation = []
    if "all_sessions" not in st.session_state:
        st.session_state.all_sessions = []
    if "retry_query" not in st.session_state:
        st.session_state.retry_query = None
    if "session_names" not in st.session_state:
        st.session_state.session_names = {}
    if "composer_text" not in st.session_state:
        st.session_state.composer_text = ""
    if "clear_composer_on_next_run" not in st.session_state:
        st.session_state.clear_composer_on_next_run = False
    if "open_menu_session" not in st.session_state:
        st.session_state.open_menu_session = None
    if "next_sessions_refresh_at" not in st.session_state:
        st.session_state.next_sessions_refresh_at = 0.0
    if "force_sessions_refresh" not in st.session_state:
        st.session_state.force_sessions_refresh = True
    if "query_in_progress" not in st.session_state:
        st.session_state.query_in_progress = False
    if "active_index" not in st.session_state:
        st.session_state.active_index = None
    if "active_query" not in st.session_state:
        st.session_state.active_query = None
    if "session_fetch_error_count" not in st.session_state:
        st.session_state.session_fetch_error_count = 0
    if "hydrated_session_id" not in st.session_state:
        st.session_state.hydrated_session_id = None


def fetch_all_sessions(show_warning: bool = False) -> Optional[List[Dict]]:
    """Fetch all available sessions from backend."""
    try:
        response = requests.get(f"{SESSIONS_ENDPOINT}?limit=25", timeout=SESSIONS_TIMEOUT_SECONDS)
        response.raise_for_status()
        st.session_state.session_fetch_error_count = 0
        return response.json()
    except requests.exceptions.RequestException:
        st.session_state.session_fetch_error_count += 1
        if show_warning and st.session_state.session_fetch_error_count <= 1:
            st.sidebar.caption("Session list is temporarily unavailable. Showing last loaded chats.")
        return None


def fetch_session_history(session_id: str) -> List[Dict]:
    """Fetch chat history for a specific session."""
    try:
        response = requests.get(f"{HISTORY_ENDPOINT}/{session_id}?limit=25", timeout=SESSIONS_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        return data.get("chats", [])
    except requests.exceptions.RequestException as e:
        st.warning("Could not load session history right now.")
        return []


def normalize_response_payload(response: Dict) -> Dict:
    """Return the backend payload as a plain dict, unwrapping wrapper keys when needed."""
    if isinstance(response, dict):
        if isinstance(response.get("answer"), dict):
            return response["answer"]
        if isinstance(response.get("result"), dict):
            return response["result"]
        return response

    if isinstance(response, str):
        try:
            parsed = ast.literal_eval(response)
            if isinstance(parsed, dict):
                return normalize_response_payload(parsed)
        except (ValueError, SyntaxError):
            return {}

    return {}


def delete_session_history(session_id: str) -> bool:
    """Delete a session via backend API."""
    try:
        response = requests.delete(f"{HISTORY_ENDPOINT}/{session_id}", timeout=SESSIONS_TIMEOUT_SECONDS)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        st.warning("Could not delete this chat right now.")
        return False


def send_query(query: str, session_id: str) -> Optional[Dict]:
    """Send a query to the backend and get response."""
    try:
        payload = {
            "query": query,
            "session_id": session_id
        }
        response = requests.post(QUERY_ENDPOINT, json=payload, timeout=(5, QUERY_TIMEOUT_SECONDS))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ReadTimeout:
        st.error(
            "The backend is taking too long to respond. "
            "Please try again in a few seconds, or simplify the query."
        )
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to send query: {str(e)}")
        return None


def render_bullet_list(items: List[str]):
    """Render a list as concise bullet points."""
    for item in items:
        st.markdown(f"- {item}")


def build_primary_answer_text(response: Dict) -> str:
    """Build the always-visible top answer for the assistant response."""
    payload = normalize_response_payload(response)

    if not payload:
        return ""

    if payload.get("emergency_services"):
        location = payload.get("location", "")
        service_type = payload.get("emergency_type", "service")
        intro = payload.get("message") or (
            f"Here are nearby {service_type.lower()} services"
            + (f" in {location.title()}" if location else "")
            + ":"
        )
        lines = [intro, ""]
        seen = set()
        service_count = 0
        for service in payload.get("emergency_services", []):
            if isinstance(service, dict):
                name = service.get("name", "Unknown service")
                address = service.get("address", "Address not available")
                key = (str(name).strip().lower(), str(address).strip().lower())
                if key in seen:
                    continue
                seen.add(key)
                service_count += 1
                lines.append(f"{service_count}. **{name}**")
                if address and address.lower() not in str(name).lower():
                    lines.append(f"   {address}")
            else:
                service_text = str(service).strip()
                if service_text:
                    if service_text.lower() not in seen:
                        seen.add(service_text.lower())
                        service_count += 1
                        lines.append(f"{service_count}. {service_text}")
        return "\n".join(lines).strip()

    if payload.get("explanation"):
        return str(payload.get("explanation", "")).strip()

    if payload.get("message"):
        return str(payload.get("message", "")).strip()

    if payload.get("draft"):
        return str(payload.get("message") or "Here is a draft complaint / FIR based on your situation.").strip()

    if payload.get("lawyers"):
        return str(payload.get("message") or "Here are the lawyers I found for you.").strip()

    return ""


def render_response_sections(response: Dict, key_prefix: str = ""):
    """Render secondary response sections using progressive disclosure."""
    payload = normalize_response_payload(response)
    if not payload:
        st.markdown("No details available.")
        return

    def section_has_items(value):
        return bool(value)

    legal_references = payload.get("legal_references") or []
    if section_has_items(legal_references):
        st.markdown("### 📋 Legal References")
        for ref in legal_references:
            if isinstance(ref, dict):
                section = ref.get("section", "")
                title = ref.get("title", "Unknown Law")
                description = ref.get("description", "")
                category = ref.get("category", "")
                line = f"**{section} - {title}**" if section else f"**{title}**"
                st.markdown(line)
                if description:
                    st.markdown(f"- {description}")
                if category:
                    st.caption(f"Category: {category}")
            else:
                st.markdown(f"- {ref}")

    relevant_laws = payload.get("relevant_laws") or []
    if section_has_items(relevant_laws):
        st.markdown("### ⚖️ Relevant Laws")
        for law in relevant_laws:
            if isinstance(law, dict):
                title = law.get("title", "Unknown Law")
                section = law.get("section", "")
                text = law.get("text", "")
                heading = f"**{title}**"
                if section:
                    heading += f" (Section {section})"
                st.markdown(heading)
                if text:
                    st.markdown(f"- {text}")
            else:
                st.markdown(f"- {law}")

    related_cases = payload.get("related_cases") or []
    recent_cases = payload.get("recent_cases") or []
    if section_has_items(related_cases) or section_has_items(recent_cases):
        st.markdown("### 📚 Case Laws")
        if related_cases:
            for case in related_cases:
                if isinstance(case, dict):
                    headline = case.get("headline", "No headline")
                    url = case.get("url", "")
                    if url:
                        st.markdown(f"- [{headline}]({url})")
                    else:
                        st.markdown(f"- {headline}")
                else:
                    st.markdown(f"- {case}")
        if recent_cases:
            for case in recent_cases:
                if isinstance(case, dict):
                    title = case.get("title", "Unknown Case")
                    citation = case.get("citation", "")
                    summary = case.get("summary", "")
                    line = f"- **{title}**"
                    if citation:
                        line += f" ({citation})"
                    st.markdown(line)
                    if summary:
                        st.markdown(f"  - {summary}")
                else:
                    st.markdown(f"- {case}")

    possible_scenarios = payload.get("possible_scenarios") or []
    if section_has_items(possible_scenarios):
        st.markdown("### 🔍 Possible Scenarios")
        render_bullet_list([str(item) for item in possible_scenarios])

    lawyers = payload.get("lawyers") or []
    if section_has_items(lawyers):
        st.markdown("### 👩‍⚖️ Nearby Lawyers")
        for lawyer in lawyers:
            if isinstance(lawyer, dict):
                name = lawyer.get("name", "Unknown")
                specialization = lawyer.get("specialization", "")
                location = lawyer.get("location", "")
                contact = lawyer.get("contact", "")
                parts = [f"**{name}**"]
                if specialization:
                    parts.append(specialization)
                if location:
                    parts.append(location)
                if contact:
                    parts.append(f"📞 {contact}")
                st.markdown(" | ".join(parts))
            else:
                st.markdown(f"- {lawyer}")

    draft = payload.get("draft")
    if draft:
        st.markdown("### 📝 Draft Complaint / FIR")
        if isinstance(draft, dict):
            draft_category = draft.get("category", "")
            draft_content = draft.get("content", "")
            if draft_category:
                st.caption(f"Category: {draft_category}")
            if draft_content:
                st.markdown(draft_content)
        elif isinstance(draft, str):
            st.markdown(draft)

    # Penultimate section.
    suggestions = payload.get("suggestions") or []
    if section_has_items(suggestions):
        st.markdown("### 💡 Suggestions")
        render_bullet_list([str(item) for item in suggestions])

    # Ultimate section.
    disclaimer = payload.get("disclaimer")
    if disclaimer:
        st.markdown("### ⚠️ Disclaimer")
        st.markdown(str(disclaimer))


def render_assistant_response(response: Dict, stream_main_answer: bool = False, key_prefix: str = ""):
    """Render assistant response in a structured chat card."""
    payload = normalize_response_payload(response)
    primary_answer = build_primary_answer_text(payload)

    if primary_answer:
        if stream_main_answer:
            st.write_stream(stream_chunks(primary_answer))
        else:
            st.markdown(primary_answer)

    actions = payload.get("recommended_actions") or payload.get("suggested_actions") or []
    if actions:
        st.markdown("### ✅ What You Can Do")
        for action in actions:
            st.markdown(f"- {action}")

    has_secondary_sections = any(payload.get(key) for key in [
        "legal_references", "relevant_laws", "related_cases", "recent_cases",
        "possible_scenarios", "lawyers", "draft", "suggestions", "disclaimer"
    ])

    if has_secondary_sections:
        st.markdown("---")

    # Optional summary line before expanders.
    if any(payload.get(key) for key in [
        "legal_references", "relevant_laws", "related_cases", "recent_cases",
        "possible_scenarios", "lawyers", "draft", "suggestions", "disclaimer"
    ]):
        st.caption("Here’s what I found based on your situation:")

    render_response_sections(payload, key_prefix=key_prefix)


def format_response(response: Dict) -> str:
    """Format the response for display."""
    if isinstance(response, str):
        # Some backends return dict-like strings; parse safely before formatting.
        try:
            parsed = ast.literal_eval(response)
            if isinstance(parsed, dict):
                return format_complex_response(parsed)
        except (ValueError, SyntaxError):
            return response

    if isinstance(response, dict):
        if "answer" in response:
            answer_payload = response["answer"]
            if isinstance(answer_payload, dict):
                return format_complex_response(answer_payload)
            return str(answer_payload)
        if "result" in response:
            result_payload = response["result"]
            if isinstance(result_payload, dict):
                return format_complex_response(result_payload)
            return str(result_payload)
        return format_complex_response(response)

    return str(response)


def format_complex_response(response: Dict) -> str:
    """Format complex responses with laws, cases, etc."""
    output = ""

    if "emergency_services" in response and response["emergency_services"]:
        location = response.get("location", "")
        service_type = response.get("emergency_type", "service")
        if location:
            output += f"Here are nearby {service_type} services in {location.title()}:\n\n"
        else:
            output += f"Here are nearby {service_type} services:\n\n"
        for idx, service in enumerate(response["emergency_services"], start=1):
            if isinstance(service, dict):
                name = service.get("name", "Unknown service")
                address = service.get("address", "Address not available")
                output += f"{idx}. **{name}**\n"
                output += f"   - {address}\n"
            else:
                output += f"{idx}. {service}\n"
        output += "\n"

    if response.get("message"):
        output += f"{response['message']}\n\n"

    if "draft" in response and response["draft"]:
        output += "### 📝 Draft Complaint / FIR\n"
        draft_payload = response["draft"]
        if isinstance(draft_payload, dict):
            draft_content = draft_payload.get("content", "")
            draft_category = draft_payload.get("category", "")
            if draft_category:
                output += f"- Category: **{draft_category}**\n\n"
            if draft_content:
                output += f"```text\n{draft_content}\n```\n\n"
        elif isinstance(draft_payload, str):
            output += f"```text\n{draft_payload}\n```\n\n"

    if "lawyers" in response and response["lawyers"]:
        output += "### 👩‍⚖️ Lawyers\n"
        for lawyer in response["lawyers"]:
            if isinstance(lawyer, dict):
                name = lawyer.get("name", "Unknown")
                specialization = lawyer.get("specialization", "")
                location = lawyer.get("location", "")
                contact = lawyer.get("contact", "")
                output += f"- **{name}**"
                if specialization:
                    output += f" | {specialization}"
                if location:
                    output += f" | {location}"
                if contact:
                    output += f" | 📞 {contact}"
                output += "\n"
            else:
                output += f"- {lawyer}\n"
        output += "\n"

    if response.get("intent"):
        output += f"### 🎯 Detected Intent\n- {response['intent']}\n\n"

    if response.get("query"):
        output += f"### ❓ Query\n{response['query']}\n\n"
    
    # Laws
    if "legal_references" in response and response["legal_references"]:
        output += "### 📋 Legal References\n"
        for law in response["legal_references"]:
            if isinstance(law, dict):
                section = law.get("section", "")
                title = law.get("title", "Unknown Law")
                description = law.get("description", "")
                category = law.get("category", "")
                heading = f"**{section} - {title}**" if section else f"**{title}**"
                output += f"{heading}\n"
                if description:
                    output += f"{description}\n"
                if category:
                    output += f"_Category: {category}_\n"
                output += "\n"

    if "relevant_laws" in response and response["relevant_laws"]:
        output += "### 📋 Relevant Laws\n"
        for law in response["relevant_laws"]:
            if isinstance(law, dict):
                title = law.get("title", "Unknown Law")
                section = law.get("section", "")
                text = law.get("text", "")
                output += f"**{title}**"
                if section:
                    output += f" (Section {section})"
                output += f"\n{text}\n\n"
            else:
                output += f"- {law}\n"
    
    # Explanation
    if "explanation" in response:
        output += f"### 📝 Explanation\n{response['explanation']}\n\n"
    
    # Possible Scenarios
    if "possible_scenarios" in response and response["possible_scenarios"]:
        output += "### 🔍 Possible Scenarios\n"
        for scenario in response["possible_scenarios"]:
            output += f"- {scenario}\n"
        output += "\n"
    
    # Recent Cases
    if "related_cases" in response and response["related_cases"]:
        output += "### ⚖️ Related Cases\n"
        for case in response["related_cases"]:
            if isinstance(case, dict):
                headline = case.get("headline", "No headline")
                url = case.get("url", "")
                output += f"- **{headline}**"
                if url:
                    output += f" ([source]({url}))"
                output += "\n"
            else:
                output += f"- {case}\n"
        output += "\n"

    if "recent_cases" in response and response["recent_cases"]:
        output += "### ⚖️ Recent Cases\n"
        for case in response["recent_cases"]:
            if isinstance(case, dict):
                title = case.get("title", "Unknown Case")
                citation = case.get("citation", "")
                summary = case.get("summary", "")
                output += f"**{title}**"
                if citation:
                    output += f" ({citation})"
                output += f"\n{summary}\n\n"
            else:
                output += f"- {case}\n"
    
    # Suggested Actions
    if "recommended_actions" in response and response["recommended_actions"]:
        output += "### ✅ Recommended Actions\n"
        for action in response["recommended_actions"]:
            output += f"- {action}\n"
        output += "\n"

    if "suggested_actions" in response and response["suggested_actions"]:
        output += "### ✅ Suggested Actions\n"
        for action in response["suggested_actions"]:
            output += f"- {action}\n"
        output += "\n"

    if "suggestions" in response and response["suggestions"]:
        output += "### 💡 Next Suggestions\n"
        for suggestion in response["suggestions"]:
            output += f"- {suggestion}\n"
        output += "\n"
    
    # Disclaimer
    if "disclaimer" in response:
        output += f"### ⚠️ Disclaimer\n*{response['disclaimer']}*\n"
    
    return output if output else f"```json\n{json.dumps(response, indent=2, default=str)}\n```"


def stream_chunks(text: str, chunk_size: int = 24, delay_seconds: float = 0.07) -> Iterator[str]:
    """Yield text word-by-word for typewriter-like streaming output."""
    if not text:
        return
    tokens = re.findall(r"\S+\s*|\n", text)
    for token in tokens:
        if delay_seconds > 0:
            time.sleep(delay_seconds)
        yield token


def history_to_conversation(history: List[Dict]) -> List[Dict]:
    """Convert API history rows to UI conversation turns (oldest to newest)."""
    conversation = []
    for chat in reversed(history):
        query = chat.get("query", "")
        timestamp = chat.get("timestamp", "")
        response = chat.get("response", {})
        conversation.append(
            {
                "query": query,
                "timestamp": str(timestamp) if timestamp else "",
                "response": response,
                "status": "done",
            }
        )
    return conversation


def make_session_name_from_query(query: str, session_id: str) -> str:
    """Create a readable unique session name from first user query words."""
    words = re.findall(r"[A-Za-z0-9]+", (query or ""))
    stopwords = {
        "i", "me", "my", "a", "an", "the", "is", "am", "are", "was", "were",
        "to", "for", "of", "in", "on", "at", "with", "and", "or", "by", "please",
        "can", "could", "would", "should", "do", "does", "did", "have", "has", "had",
        "help", "need", "want"
    }
    filtered = [w for w in words if w.lower() not in stopwords]
    core_words = filtered[:3] if filtered else words[:3]
    readable = " ".join(w.capitalize() for w in core_words if w)
    if not readable:
        readable = "New Chat"
    unique_suffix = (session_id or "")[-4:].upper()
    return f"{readable} - {unique_suffix}"


def ensure_session_name(session_id: str):
    """Ensure each session has a readable label; derive from first query when possible."""
    if session_id in st.session_state.session_names:
        return

    history = fetch_session_history(session_id)
    first_query = ""
    if history:
        # API returns newest first, so oldest turn is last item.
        first_query = history[-1].get("query", "")
    st.session_state.session_names[session_id] = make_session_name_from_query(first_query, session_id)


def render_conversation(conversation: List[Dict]):
    """Render full chat with retry action for each assistant response."""
    if not conversation:
        st.info("Start by asking a question.")
        return

    for idx, turn in enumerate(conversation):
        query = turn.get("query", "")
        response_payload = turn.get("response")
        status = str(turn.get("status", "done"))

        # User message with custom bubble (no chat container, so no white card behind it)
        st.markdown(f'''<div class="user-bubble">{query}</div>''', unsafe_allow_html=True)

        # Assistant message with custom bubble
        with st.chat_message("assistant", avatar="⚖️"):
            if status == "thinking":
                st.markdown("⏳ Thinking...")
            elif response_payload is None:
                st.markdown("No response available.")
            else:
                with st.container():
                    render_assistant_response(response_payload, stream_main_answer=False, key_prefix=f"history_{idx}")
                if st.button("Retry", key=f"retry_{idx}"):
                    st.session_state.retry_query = query
                    st.rerun()


def sidebar_session_manager():
    """Manage session selection in sidebar."""
    st.sidebar.markdown("## 💬 Chat History")
    
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.conversation = []
        st.session_state.retry_query = None
        st.session_state.query_in_progress = False
        st.session_state.active_index = None
        st.session_state.active_query = None
        st.session_state.session_names.setdefault(
            st.session_state.session_id,
            make_session_name_from_query("", st.session_state.session_id),
        )
        st.rerun()
    
    # Fetch sessions only when needed (avoids API spam during rerun loops).
    now_ts = time.time()
    should_refresh = (
        st.session_state.force_sessions_refresh
        or not st.session_state.all_sessions
        or (
            (not st.session_state.query_in_progress)
            and now_ts >= float(st.session_state.next_sessions_refresh_at)
        )
    )

    if should_refresh:
        sessions = fetch_all_sessions(show_warning=False)
        if sessions is not None:
            st.session_state.all_sessions = sessions
            st.session_state.next_sessions_refresh_at = now_ts + 30
            st.session_state.force_sessions_refresh = False
    
    if st.session_state.all_sessions:
        st.sidebar.markdown("**Chats**")

        for idx, session in enumerate(st.session_state.all_sessions[:25]):
            session_id = session.get("session_id", "")
            timestamp = session.get("timestamp", "")
            ensure_session_name(session_id)
            session_name = st.session_state.session_names.get(
                session_id,
                make_session_name_from_query("", session_id),
            )

            if timestamp:
                try:
                    ts = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M")
                except:
                    ts = timestamp
            else:
                ts = "Unknown"

            is_current = session_id == st.session_state.session_id
            row = st.sidebar.columns([8, 2])
            with row[0]:
                label = f"{'● ' if is_current else ''}{session_name}"
                if st.button(
                    label,
                    key=f"session_btn_{idx}_{session_id}",
                    use_container_width=True,
                    type="primary" if is_current else "secondary",
                ):
                    if not is_current:
                        st.session_state.session_id = session_id
                        history = fetch_session_history(session_id)
                        st.session_state.conversation = history_to_conversation(history)
                        st.session_state.retry_query = None
                        st.session_state.query_in_progress = False
                        st.session_state.active_index = None
                        st.session_state.active_query = None
                        st.rerun()
            with row[1]:
                if st.button("⋯", key=f"menu_btn_{idx}_{session_id}", use_container_width=True, type="tertiary"):
                    if st.session_state.open_menu_session == session_id:
                        st.session_state.open_menu_session = None
                    else:
                        st.session_state.open_menu_session = session_id
                    st.rerun()

                if st.session_state.open_menu_session == session_id:
                    if st.button("Delete chat", key=f"delete_{idx}_{session_id}", use_container_width=True, type="secondary"):
                        if delete_session_history(session_id):
                            if session_id == st.session_state.session_id:
                                st.session_state.session_id = str(uuid.uuid4())
                                st.session_state.conversation = []
                                st.session_state.query_in_progress = False
                                st.session_state.active_index = None
                                st.session_state.active_query = None
                            st.session_state.session_names.pop(session_id, None)
                            st.session_state.open_menu_session = None
                            st.session_state.force_sessions_refresh = True
                            st.rerun()
    else:
        st.sidebar.info("No previous chats yet. Start a new conversation!")


def main():
    """Main Streamlit app."""
    initialize_session_state()
    
    # Sidebar
    sidebar_session_manager()

    # Hydrate from backend only once per selected session and never during in-flight query updates.
    if (
        st.session_state.session_id
        and st.session_state.hydrated_session_id != st.session_state.session_id
        and not st.session_state.query_in_progress
    ):
        history = fetch_session_history(st.session_state.session_id)
        st.session_state.conversation = history_to_conversation(history) if history else []
        st.session_state.hydrated_session_id = st.session_state.session_id
    
    pending_retry = st.session_state.retry_query
    if st.session_state.clear_composer_on_next_run:
        st.session_state.composer_text = ""
        st.session_state.clear_composer_on_next_run = False
    if pending_retry:
        st.session_state.composer_text = pending_retry
        st.session_state.retry_query = None

    # Main content
    if not st.session_state.conversation:
        st.markdown(
            """
            <div class="hero-shell">
                <div class="hero-title">⚖️ NYAYA SAATHI - Your Legal AI Consultant </div>
                <div class="hero-subtitle">Ask a legal question. Get a focused answer, then the details.</div>
                <div class="hero-copy">
                    A chat-style legal assistant for urgent help, complaint drafting, case references, and practical next steps.
                    The main answer appears first, while supporting laws, cases, lawyers, and drafts stay tucked into expanders.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_conversation(st.session_state.conversation)

    with st.form(key="chat_form", clear_on_submit=False):
        col1, col2 = st.columns([9, 1])

        with col1:
            user_input = st.text_input(
                "Message",
                placeholder="e.g., My landlord is not returning my deposit, what can I do?",
                label_visibility="collapsed",
                key="composer_text",
                disabled=st.session_state.query_in_progress,
            )

        with col2:
            action_clicked = st.form_submit_button("➤", use_container_width=True, disabled=st.session_state.query_in_progress)

    query_to_send = (user_input or "").strip()
    if action_clicked and query_to_send and not st.session_state.query_in_progress:
        last_turn = st.session_state.conversation[-1] if st.session_state.conversation else None
        if last_turn and last_turn.get("query", "") == query_to_send and last_turn.get("status") == "thinking":
            st.rerun()

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.conversation.append(
            {
                "query": query_to_send,
                "timestamp": current_time,
                "response": None,
                "status": "thinking",
            }
        )
        if len(st.session_state.conversation) == 1:
            st.session_state.session_names[st.session_state.session_id] = make_session_name_from_query(
                query_to_send,
                st.session_state.session_id,
            )
        st.session_state.active_index = len(st.session_state.conversation) - 1
        st.session_state.active_query = query_to_send
        st.session_state.query_in_progress = True
        st.session_state.clear_composer_on_next_run = True
        st.rerun()

    # Execute backend and update the same conversation row in place.
    if st.session_state.query_in_progress and st.session_state.active_index is not None:
        index = int(st.session_state.active_index)
        query_for_index = st.session_state.active_query or ""
        if 0 <= index < len(st.session_state.conversation):
            query_for_index = st.session_state.conversation[index].get("query", "") or query_for_index

        if query_for_index:
            response = send_query(query_for_index, st.session_state.session_id)

            if response is not None:
                if 0 <= index < len(st.session_state.conversation):
                    st.session_state.conversation[index]["response"] = response
                    st.session_state.conversation[index]["status"] = "done"
                else:
                    st.session_state.conversation.append(
                        {
                            "query": query_for_index,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "response": response,
                            "status": "done",
                        }
                    )
                st.session_state.force_sessions_refresh = True
                st.session_state.retry_query = None
            else:
                failure_payload = {
                    "message": "I could not fetch a response just now. Please retry.",
                    "disclaimer": "Temporary network or server issue."
                }
                if 0 <= index < len(st.session_state.conversation):
                    st.session_state.conversation[index]["response"] = failure_payload
                    st.session_state.conversation[index]["status"] = "done"
                else:
                    st.session_state.conversation.append(
                        {
                            "query": query_for_index,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "response": failure_payload,
                            "status": "done",
                        }
                    )

        st.session_state.query_in_progress = False
        st.session_state.active_index = None
        st.session_state.active_query = None
        st.rerun()
    
    # Footer
    st.divider()
    st.markdown(
        """
        <div class="footer-shell">
            <div style='text-align: center; color: #475569; font-size: 0.9rem; line-height: 1.55;'>
            <div><strong>Nyaya Saathi v1.0</strong> | Powered by LangGraph & LLMs</div>
            <div>⚠️ This is an AI-powered assistant, not a substitute for professional legal advice.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
