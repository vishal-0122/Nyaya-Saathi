import json
import os
import re
from typing import Dict

LEGAL_DATA_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../data/raw/legal_data.json"
)


def load_legal_sections(category: str) -> list:
    try:
        with open(LEGAL_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        return [
            s for s in data
            if s.get("category", "").lower() == category.lower()
        ]
    except Exception:
        return []


def detect_category(query: str) -> str:
    q = query.lower()
    keywords = {
        "defamation": "Defamation",
        "defame": "Defamation",
        "accident": "Traffic",
        "hit by a car": "Traffic",
        "hit by a truck": "Traffic",
        "hit by a bus": "Traffic",
        "hit and run": "Traffic",
        "traffic": "Traffic",
        "fraud": "Fraud",
        "cheating": "Fraud",
        "cheated": "Fraud",
        "scam": "Fraud",
        "online": "Fraud",
        "cyber": "Fraud",
        "forgery": "Forgery",
        "theft": "Property",
        "property": "Property",
        "assault": "Violence",
        "hurt": "Violence",
        "violence": "Violence",
        "police misuse": "Police Misuse",
    }

    for k, v in keywords.items():
        if k in q:
            return v

    return "General"


def _clean_incident_text(query: str, category: str) -> str:
    text = (query or "").strip()

    # If text contains the multi-line instruction format, extract just the prior context
    if "Prior incident context:" in text and "Current request:" in text:
        lines = text.split("\n")
        for line in lines:
            if line.startswith("Prior incident context:"):
                text = line.replace("Prior incident context:", "").strip()
                break
        if not text or text.startswith("Current"):
            # Fallback: look for the first substantive line
            for line in lines:
                if line.strip() and not line.startswith(("Prior", "Current", "Generate")):
                    text = line.strip()
                    break

    # Aggressive patterns to remove draft command prefixes
    patterns = [
        r"^(please\s+)?(draft|write|prepare|make)\s+(me\s+)?(a(n)?\s+)?(an?\s+)?fir\s+(draft\s+)?(against|to)",
        r"^(please\s+)?(draft|write|prepare|make)\s+(me\s+)?(a(n)?\s+)?.*(draft|complaint|fir|application|letter)\s+(against|to|for|regarding)",
        r"^(please\s+)?(draft|write|prepare|make)\s+me\s+(an?\s+)?",
        r"^(please\s+)?(draft|write|prepare|make)\s+for\s+(an?\s+)?",
        r"^(please\s+)?draft\s+for\s+",
        r"^(please\s+)?give\s+me\s+(an?\s+)?",
        r"^(please\s+)?draft\s+to\s+register",
        r"^(draft|write)\s+a(n)?\s+(draft|complaint|fir|application|letter)",
        r"\bto\s+register\s+(an?\s+)?fir\b",
        r"\bfor\s+registering\s+(an?\s+)?fir\b",
        r"\bto\s+register\s+(an?\s+)?(police\s+)?complaint\b",
    ]
    for p in patterns:
        text = re.sub(p, "", text, flags=re.IGNORECASE).strip()

    text = re.sub(r"^(for\s+)?(a|an)\s+", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\s+case\b", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\s+", " ", text).strip(" .,")

    accused = None
    # Extract accused person if mentioned
    match = re.search(r"against\s+([A-Za-z][A-Za-z\s]{1,50})", query or "", re.IGNORECASE)
    if match:
        accused = match.group(1).strip().rstrip(".,").strip()

    is_command_like = bool(re.search(r"\b(draft|write|prepare|make|complaint|fir|application|letter)\b", query or "", re.IGNORECASE))

    if category == "Defamation":
        if accused:
            return (
                f"I wish to lodge a complaint regarding defamatory statements and harm to reputation allegedly caused by {accused}. "
                "These statements have adversely affected my social and professional standing."
            )
        return (
            "I wish to lodge a complaint regarding defamatory statements and harm to my reputation. "
            "These statements have adversely affected my social and professional standing."
        )

    if category == "Traffic" and is_command_like:
        if accused:
            return (
                f"I was involved in a traffic incident caused by {accused}. "
                "The incident resulted in damage and harm to my person."
            )
        return (
            "I was involved in a traffic incident. The incident resulted in damage and harm to my person."
        )

    if category == "Property" and is_command_like:
        if accused:
            return (
                f"I wish to lodge a complaint regarding theft and unlawful interference with my property allegedly committed by {accused}. "
                "The incident caused financial loss and distress."
            )
        return (
            "I wish to lodge a complaint regarding theft and unlawful interference with my property. "
            "The incident caused financial loss and distress."
        )

    if text:
        return text[0].upper() + text[1:] if len(text) > 1 else text

    return "[Brief description of the incident]"


def generate_draft(query: str) -> dict:
    category = detect_category(query)
    incident_description = _clean_incident_text(query, category)

    sections = load_legal_sections(category)

    if sections:
        sections_text = "\n".join([
            f"- {s['section']}: {s['title']} - {s['description']}"
            for s in sections
        ])
    else:
        sections_text = ""

    draft = f"""
To,
The Officer-in-Charge,
[Police Station Name],
[City/District]

Subject: Complaint regarding {category} incident

Respected Sir/Madam,

I, [Your Name], resident of [Your Address], respectfully submit this complaint for registration of an FIR.

Date of Incident: [Date of Incident]
Time of Incident: [Time of Incident]
Place of Incident: [Place of Incident]

Brief Facts of the Incident:
{incident_description}

Persons Involved (if known): [Name(s) / Unknown]
Witnesses (if any): [Witness details]

Relevant Sections:
{sections_text}

I request you to kindly register this complaint and take appropriate action as per law.

Yours faithfully,
[Your Name]
"""

    return {
        "draft": draft.strip(),
        "category": category
    }