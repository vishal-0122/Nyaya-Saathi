import json
import re
import logging
from langsmith import traceable

from app.core.llm.openai_client import get_llm
from app.utils.prompts import get_reasoning_prompt
from app.models.response import LegalResponse
from langchain_core.output_parsers import PydanticOutputParser


def _extract_location(text: str) -> str:
    match = re.search(r"(?:in|from|at|near|around|within)\s+([A-Za-z\s]+)", text or "", re.IGNORECASE)
    if match:
        return match.group(1).strip().rstrip(".,")
    return ""

# structured output issue needs to be resolved and mcp is not reachable at 8001 port

@traceable(name="reasoning_node", run_type="chain")
def reasoning_node(state: dict) -> dict:
    try:
        query = state.get("query", "")
        docs = state.get("docs", []) or []
        cases = state.get("cases", []) or []
        intent = (state.get("intent") or "").lower()

        # Normalize docs from different retrieval shapes.
        # Supported:
        # 1) {"section": ..., "title": ..., "description": ..., "category": ...}
        # 2) {"description": ..., "metadata": {"section": ..., "title": ..., "category": ..., "description": ...}}
        normalized_docs = []
        for doc in docs:
            if isinstance(doc, dict):
                meta = doc.get("metadata") if isinstance(doc.get("metadata"), dict) else {}
                section = doc.get("section") or meta.get("section") or ""
                title = doc.get("title") or meta.get("title") or ""
                description = doc.get("description") or meta.get("description") or ""
                category = doc.get("category") or meta.get("category") or ""
                normalized_docs.append({
                    "section": section,
                    "title": title,
                    "description": description,
                    "category": category,
                })
            else:
                normalized_docs.append({
                    "section": "",
                    "title": "",
                    "description": str(doc),
                    "category": "",
                })

        docs = normalized_docs
# emergency service needs a structured output as well as about the location and type of emergency 
        # =========================
        # 💬 GENERAL QUERY INTENT
        # =========================
        if intent == "general_query":
            llm = get_llm()
            prompt = f"""
You are a polite, humble assistant.

Reply to the user in 2 to 3 short lines only.
Do not ask any follow-up questions.
Do not mention laws, legal facts, sections, or analysis.
Keep it conversational, minimal, and respectful.
Do not invent facts about the query.
End with a gentle sentence like "hanks for reaching out. I’m here to help if you need anything legal or related to this matter. If you want any legal information, please tell me and I’ll assist you" inviting them to ask for legal information only or any hospital or police station addresses if needed.

User query: {query}
"""

            try:
                response = llm.invoke(prompt)
                message = getattr(response, "content", str(response)).strip()
            except Exception:
                message = "Thanks for reaching out. I’m here to help if you need anything legal or related to this matter. If you want any legal information, please tell me and I’ll assist you respectfully."

            state["answer"] = {
                "message": message
            }
            return state

        # =========================
        # 🧑‍⚖️ LAWYER LOOKUP INTENT
        # =========================
        if intent == "lawyer_lookup":
            lawyers = state.get("lawyers", [])
            # Extract count from query for display (default 3)
            count = 3
            count_match = re.search(r"(\d+)\s+lawyers?", query, re.IGNORECASE)
            if count_match:
                count = int(count_match.group(1))
            elif re.search(r"some\s+lawyers?", query, re.IGNORECASE):
                count = 5
            elif re.search(r"few\s+lawyers?", query, re.IGNORECASE):
                count = 3
            state["answer"] = {
                "message": "Here are some lawyers you can contact immediately.",
                "lawyers": lawyers[:count],
                # "disclaimer": "This is not legal advice."
            }
            return state
        
        # For all other intents, do not delete lawyers from state, but ensure they are not included in the response
        # Remove 'lawyers' from state['answer'] if present (defensive)

        # =========================
        # 🚨 EMERGENCY INTENT
        # =========================
        emergency_services = state.get("emergency_services", []) or []
        emergency_error = state.get("emergency_error", "")
        plan = state.get("plan", {})
        location = state.get("location") or (plan.get("location", "") if isinstance(plan, dict) else "")
        query_lower = query.lower()
        if any(k in query_lower for k in ["hospital", "ambulance", "injury", "doctor"]):
            emergency_type = "hospital"
        elif any(k in query_lower for k in ["police", "theft", "robbery", "assault", "crime"]):
            emergency_type = "police"
        else:
            emergency_type = "emergency"

        if not location:
            match = re.search(r"(?:in|from|at)\s+([A-Za-z\s]+)", query, re.IGNORECASE)
            if match:
                location = match.group(1).strip().rstrip(".,")
        # If location is missing or too generic, ask for more detail
        if intent == "emergency":
            if not location:
                conversation_context = state.get("conversation_context", "") or ""
                location = _extract_location(f"{query}\n{conversation_context}")

            if not location:
                state["answer"] = {
                    "message": f"Please specify the area or locality where you need {emergency_type} addresses.",
                    "emergency_type": emergency_type,
                    "location": location or "",
                    "emergency_services": [],
                    # "disclaimer": "This is not legal advice. Please consult a qualified lawyer."
                }
                return state

            # Optionally filter results to match location more strictly
            filtered = [s for s in emergency_services if location.lower() in s.get("address", "").lower()]
            final_services = filtered if filtered else emergency_services

            live_services = [
                s for s in final_services
                if s.get("source") != "fallback" and not str(s.get("name", "")).lower().startswith("no live")
            ]

            if not final_services or not live_services:
                message = f"I could not fetch live {emergency_type} addresses right now for {location.title()}. Please try again in a moment."
                if emergency_error:
                    message = f"I could not fetch live {emergency_type} addresses right now for {location.title()} due to a temporary service issue. Please try again in a moment."
                state["answer"] = {
                    "message": message,
                    "emergency_type": emergency_type,
                    "location": location,
                    "emergency_services": [],
                    # "disclaimer": "This is not legal advice. Please consult a qualified lawyer."
                }
                return state

            state["answer"] = {
                "message": f"Here are nearby {emergency_type} services in {location.title()}:",
                "emergency_type": emergency_type,
                "location": location,
                "emergency_services": live_services,
                # "disclaimer": "This is not legal advice. Please consult a qualified lawyer."
            }
            return state

        # =========================
        # 📚 CASE SEARCH INTENT (handled after LLM call)
        # =========================

        # =========================
        # 🧠 MAIN LLM REASONING
        # =========================
        llm = get_llm()
        parser = PydanticOutputParser(pydantic_object=LegalResponse)
        format_instructions = parser.get_format_instructions()


        # Ensure cases_context is always a list of strings for the LLM prompt
        def case_to_str(c):
            if isinstance(c, dict):
                # Prefer headline + url for web results
                headline = c.get("headline")
                url = c.get("url")
                if headline and url:
                    return f"{headline} ({url})"
                elif headline:
                    return headline
                else:
                    return str(c)
            return str(c)

        cases_context = "\n\n".join([case_to_str(c) for c in cases]) if cases else ""

        prompt = get_reasoning_prompt(query, docs)

        if cases_context:
            prompt += f"\n\nRetrieved Cases:\n{cases_context}"

        prompt += (
            "\n\nReturn ONLY valid JSON.\n"
            f"{format_instructions}\n"
            "Do not include schema."
        )

        # =========================
        # 🔁 LLM CALL + PARSING
        # =========================
        def parse_output(content: str):
            try:
                parsed = parser.parse(content)
                output = parsed.dict()
                output.pop("disclaimer", None)
                output.pop("lawyers", None)
                return output
            except Exception:
                return None

        response = llm.invoke(prompt)
        content = getattr(response, "content", str(response))

        output = parse_output(content)

        if output is None:
            # retry once
            response = llm.invoke(prompt)
            content = getattr(response, "content", str(response))
            output = parse_output(content)

        if output is None:
            try:
                output = json.loads(content)
            except Exception:
                state["answer"] = {
                    "error": "Failed to parse LLM output",
                    "raw": content
                }
                return state

        # =========================
        # 📚 FORMAT LEGAL REFERENCES
        # =========================
        legal_references = []

        for doc in docs:
            if isinstance(doc, dict):
                legal_references.append({
                    "section": doc.get("section", ""),
                    "title": doc.get("title", ""),
                    "description": doc.get("description", ""),
                    "category": doc.get("category", "")
                })
            else:
                # fallback (if string)
                legal_references.append({
                    "section": "",
                    "title": "",
                    "description": str(doc),
                    "category": ""
                })

        # =========================
        # ⚖️ FORMAT CASES (for dynamic web results)
        # =========================
        related_cases = []
        # If cases are dicts with 'headline' and 'url', use them for related_cases (dynamic web results)
        if intent == "legal_query" and cases and isinstance(cases[0], dict) and "headline" in cases[0] and "url" in cases[0]:
            for c in cases:
                if isinstance(c, dict) and "headline" in c and "url" in c:
                    related_cases.append({
                        "headline": c["headline"],
                        "url": c["url"]
                    })
        else:
            # fallback: old format (string cases)
            for c in cases:
                if not isinstance(c, str):
                    continue
                match = re.match(r"([\w\s.]+)\((\d{4})\):\s*(.*)", c)
                if match:
                    related_cases.append({
                        "name": match.group(1).strip(),
                        "year": match.group(2),
                        "summary": match.group(3).strip()
                    })
                else:
                    related_cases.append({
                        "name": c,
                        "year": "",
                        "summary": ""
                    })

        # =========================
        # 🧩 CLEAN OUTPUT FIELDS
        # =========================
        possible_scenarios = output.get("possible_scenarios", [])
        if not isinstance(possible_scenarios, list):
            possible_scenarios = [str(possible_scenarios)]

        actions = output.get("actions", "")
        if isinstance(actions, str):
            recommended_actions = [
                a.strip() for a in re.split(r"[.\n]\s*", actions) if a.strip()
            ]
        elif isinstance(actions, list):
            recommended_actions = actions
        else:
            recommended_actions = []

        # =========================
        # 💡 SUGGESTIONS
        # =========================
        suggestions = output.get("suggestions") if isinstance(output, dict) else None

        if not suggestions:
            suggestions = state.get("suggestions", [])

        if not suggestions:
            suggestions = [
                "Do you want help finding the nearest police station?",
                "Do you want help finding the nearest hospital?",
                "Would you like contact details of any lawyers?",
                "Would you like help drafting a complaint?"
            ]

        if not isinstance(suggestions, list):
            suggestions = [str(suggestions)]

        # =========================
        # 📝 DRAFT GENERATOR INTENT
        # =========================
        if intent == "draft_generator":
            draft_value = state.get("draft", "")
            draft_category = state.get("draft_category") or state.get("category", "General")

            if isinstance(draft_value, dict):
                content_text = draft_value.get("content", "")
                if isinstance(content_text, list):
                    content_text = "\n".join(str(line) for line in content_text)
                draft_payload = {
                    "content": str(content_text),
                  #  "category": draft_value.get("category", draft_category)
                }
            else:
                content_text = str(draft_value)
                draft_payload = {
                    "content": content_text,
                    #"category": draft_category
                }

            state["answer"] = {
                "message": "Here is a draft complaint/application you can use. Please fill in your personal details before submitting to the police.",
                "draft": draft_payload,
                "disclaimer": "This draft is for informational and assistance purposes only. Please verify details and consult a qualified lawyer before submission."
            }
            return state

        # =========================
        # 🧾 FINAL RESPONSE
        # =========================
        # For legal_query, always use LLM output, but overwrite related_cases with dynamic web results if present
        answer = {
            "session_id": state.get("session_id", ""),
            "query": query,
            "intent": intent,
            "explanation": output.get("explanation", ""),
            "legal_references": legal_references,
            "related_cases": output.get("related_cases", []),
            "possible_scenarios": possible_scenarios,
            "recommended_actions": recommended_actions,
            "suggestions": suggestions,
            "disclaimer": "This is for informational purposes only. Please consult a qualified lawyer."
        }
        # Overwrite related_cases with dynamic web results if present and intent is legal_query
        if intent == "legal_query" and related_cases:
            answer["related_cases"] = related_cases
        state["answer"] = answer
        return state

    except Exception as e:
        # 🔥 NEVER crash the API
        logging.exception("Reasoning node failed")

        state["answer"] = {
            "error": "Internal reasoning error",
            "details": str(e)
        }
        return state