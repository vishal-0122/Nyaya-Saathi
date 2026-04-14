"""
Generalized Draft Generator Tool
--------------------------------
Generates a formal draft of a police complaint/application for a given crime category using user-provided details and relevant IPC sections.
"""

import json
from typing import Dict, Optional
import os

LEGAL_DATA_PATH = os.path.join(os.path.dirname(__file__), '../../data/raw/legal_data.json')

def load_legal_sections(category: str) -> list:
    """
    Load relevant IPC sections for a given category from legal_data.json.
    """
    try:
        with open(LEGAL_DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [s for s in data if s.get('category', '').lower() == category.lower()]
    except Exception:
        return []

def generate_complaint_draft(details: Dict[str, str], category: str) -> str:
    """
    Generate a formal complaint draft for police FIR registration for a given category.
    Args:
        details: Dict with keys 'name', 'date', 'time', 'place', 'incident_description'.
        category: Crime category (e.g., 'Traffic', 'Forgery', etc.)
    Returns:
        A formatted string representing the complaint draft.
    """
    incident_description = details.get('incident_description', '[Description of Incident]')

    # Load relevant IPC sections for the category
    sections = load_legal_sections(category)
    if sections:
        sections_text = '\n'.join([
            f"- {s['section']}: {s['title']} - {s['description']}" for s in sections
        ])
        section_para = f"\nRelevant IPC Sections for {category} cases include:\n{sections_text}\n"
    else:
        section_para = ''

    draft = f"""
To,
The Officer-in-Charge,
[Police Station Name],
[City/District]

Subject: Complaint regarding {category} incident on [Date of Incident] at [Place of Incident]

Respected Sir/Madam,

I, [Your Name], would like to bring to your notice the following incident:

Date: [Date of Incident]
Time: [Time of Incident]
Place: [Place of Incident]

Description of Incident:
{incident_description}
{section_para}I request you to kindly register my complaint and initiate necessary action as per law. Kindly treat this letter as my formal complaint for the registration of an FIR and the commencement of investigation.

Thank you.

Yours faithfully,
[Your Name]
"""
    return draft
