from app.core.llm.openai_client import get_llm
import json
import re
from langsmith import traceable

llm = get_llm()


@traceable(name="planner_node", run_type="chain")
def planner_node(state: dict):
    query = state.get("query", "").strip()
    print("Planner received query:", query)
    query_lower = query.lower()

    state.setdefault("retrieval_attempt", 0)
    state.setdefault("retrieval_max_attempts", 2)
    state.setdefault("retrieval_quality", "unknown")
    state.setdefault("retrieval_issues", [])
    state.setdefault("rewrite_history", [])

    # ------------------ LLM PROMPT ------------------
    prompt = f"""
    You are a legal assistant system planner.

    Analyze the user query and return ONLY valid JSON.

    Rules:
    - Choose the correct intent
    - Always return booleans (true/false)
    - Do NOT leave fields empty

    Intent definitions:
    - legal_query → general legal/legal-awareness question
    - general_query → casual or unrelated conversation
    - lawyer_lookup → user wants lawyer contacts
    - emergency → urgent help (police/hospital)
    - draft_generator → wants complaint/FIR draft

    JSON format:
    {{
        "intent": "legal_query | general_query | lawyer_lookup | emergency | draft_generator",
        "use_retrieval": true/false,
        "use_case_search": true/false,
        "use_lawyer_lookup": true/false,
        "use_emergency": true/false,
        "use_draft_generator": true/false,
        "location": string or null
    }}

    Query: {query}

    Return ONLY JSON.
    """

    response = llm.invoke(prompt)
    content = getattr(response, "content", str(response))

    # ------------------ SAFE JSON PARSE ------------------
    def safe_json_parse(text: str):
        try:
            text = text.strip()

            # remove markdown block if present
            if text.startswith("```"):
                parts = text.split("```")
                if len(parts) >= 2:
                    text = parts[1]

            return json.loads(text)
        except Exception:
            return {}

    plan = safe_json_parse(content)

    # ------------------ DEFAULT FALLBACK ------------------
    if not isinstance(plan, dict):
        plan = {}

    default_plan = {
        "intent": "legal_query",
        "use_retrieval": True,
        "use_case_search": False,
        "use_lawyer_lookup": False,
        "use_emergency": False,
        "use_draft_generator": False,
        "location": None
    }

    # merge defaults safely
    for key, value in default_plan.items():
        plan.setdefault(key, value)

    # ------------------ HEURISTIC OVERRIDES ------------------
    # Keep emergency routing for explicit emergency/service requests, including common misspellings.
    emergency_keywords = [
        "hospital", "hospitals", "hopital", "hopitals",
        "police station", "ambulance", "emergency", "urgent help",
        "need ambulance", "need police now", "medical emergency",
        "nearest hospital", "nearest police", "address of hospital", "addresses of hospital"
    ]

    category_keywords = {
        "Traffic": [
            "accident", "road accident", "car accident", "truck accident", "bus accident",
            "lorry accident", "vehicle accident", "motor vehicle", "hit and run", "collision",
            "crash", "rash driving", "drunk driving", "overspeed", "speeding", "traffic challan",
            "traffic fine", "driving licence", "license", "rc", "vehicle hit", "ran over", "run over",
            "hit by a car", "hit by a truck", "hit by", "struck by", "knocked down", "knockdown",
            "got hit", "was hit", "got struck", "car hit me", "truck hit me", "bus hit me", "struck"
        ],
        "Fraud": [
            "fraud", "scam", "scammed", "cheat", "cheated", "duped", "swindled", "con", "ponzi",
            "investment scam", "loan scam", "job scam", "matrimonial scam", "bank fraud",
            "insurance fraud", "credit card fraud", "forgery", "fake document", "impersonation",
            "cheating", "fraudulent", "fraud case", "defraud", "defrauded"
        ],
        "Cyber Crime": [
            "cyber", "cyber crime", "cyber crime", "online fraud", "phishing", "phished", "otp",
            "upi fraud", "wallet fraud", "net banking", "internet banking", "hacked", "hacking",
            "account hacked", "social media hacked", "identity theft", "digital arrest",
            "sim swap", "sextortion", "ransomware", "malware", "stolen money", "money deducted",
            "online cheating", "fake website", "fake app", "email scam", "whatsapp scam", "telegram scam"
        ],
        "Women Safety": [
            "women safety", "women safe", "domestic violence", "dowry", "dowry harassment", "stalking",
            "stalked", "eve teasing", "sexual harassment", "harassment", "molested", "molestation",
            "assault", "abused", "abuse", "threat by husband", "marital abuse", "husband abusive",
            "workplace harassment", "outraging modesty", "nri marriage issue", "girl being harassed",
            "forced marriage", "child marriage", "rape", "sexual assault", "groping", "inappropriate"
        ],
        "Property": [
            "theft", "stolen", "stole", "robbery", "robbed", "snatching", "chain snatching",
            "burglary", "break in", "break-in", "house break", "trespass", "encroachment",
            "property dispute", "land dispute", "plot dispute", "tenant", "eviction", "rent dispute",
            "phone stolen", "bike stolen", "car stolen", "vehicle stolen", "criminal trespass",
            "thief", "stealing", "robber", "burglar", "got stolen", "missing phone", "lost phone",
            "missing bike", "missing car", "property damage", "vandalism"
        ],
        "Violence": [
            "violence", "violent", "fight", "fighting", "beat", "beating", "beaten", "assault",
            "attacked", "attack", "threat", "threaten", "threats", "threatening", "intimidation",
            "kidnap", "kidnapped", "abduction", "attempt to murder", "hurt", "hurting", "grievous hurt",
            "weapon", "stab", "stabbed", "stabbing", "shoot", "shooting", "shot", "gang", "gang violence",
            "extortion", "blackmail", "blackmailed", "murdered", "murder", "killed", "killing"
        ],
        "Public Order": [
            "public nuisance", "nuisance", "rioting", "riot", "unlawful assembly", "noise complaint",
            "loudspeaker", "disturbance", "communal tension", "crowd violence", "vandalism",
            "illegal protest", "public disorder", "disturbing peace", "creating disturbance",
            "blocking road", "traffic obstruction", "blocking street"
        ],
        "Police Misuse": [
            "police harassment", "harassment by police", "false case", "false fir", "false complaint",
            "illegal detention", "custodial", "police abuse", "abusive police", "bribe by police",
            "police refused complaint", "police not filing fir", "threat by police", "misuse by police",
            "wrongful arrest", "arrested wrongfully", "false arrest", "police brutality", "beaten by police"
        ],
        "Defamation": [
            "defamation", "defamatory", "libel", "slander", "reputation", "false allegation",
            "false allegations", "false accusations", "character assassination", "character attack",
            "social media defamation", "fake post", "fake news about me", "false statement",
            "spreading lies", "false information", "defamed", "slandered", "libeled"
        ],
    }

    def has_any(keywords):
        return any(keyword in query_lower for keyword in keywords)

    explicit_emergency = has_any(emergency_keywords)

    matched_categories = [
        category for category, keywords in category_keywords.items() if has_any(keywords)
    ]

    accident_like = "Traffic" in matched_categories
    cyber_fraud_like = "Fraud" in matched_categories or "Cyber Crime" in matched_categories
    theft_or_crime_like = "Property" in matched_categories
    legal_category_detected = bool(matched_categories)

    intent_from_llm = str(plan.get("intent", "")).lower().strip()
    preserve_special_intent = intent_from_llm in {"lawyer_lookup", "draft_generator"}

    if accident_like and not explicit_emergency:
        plan["intent"] = "legal_query"
        plan["use_emergency"] = False
        plan["use_case_search"] = True
        plan["use_retrieval"] = True
        plan["use_draft_generator"] = False

    if explicit_emergency:
        plan["intent"] = "emergency"
        plan["use_emergency"] = True
        plan["use_retrieval"] = False
        plan["use_case_search"] = False
        plan["use_lawyer_lookup"] = False
        plan["use_draft_generator"] = False

    if cyber_fraud_like:
        plan["intent"] = "legal_query"
        plan["use_retrieval"] = True
        plan["use_case_search"] = True
        plan["use_emergency"] = False

    if theft_or_crime_like and not explicit_emergency:
        plan["intent"] = "legal_query"
        plan["use_retrieval"] = True
        plan["use_case_search"] = True
        plan["use_lawyer_lookup"] = False
        plan["use_emergency"] = False
        plan["use_draft_generator"] = False

    if legal_category_detected and not explicit_emergency and not preserve_special_intent:
        plan["intent"] = "legal_query"
        plan["use_retrieval"] = True
        plan["use_case_search"] = True
        plan["use_lawyer_lookup"] = False
        plan["use_emergency"] = False

    legal_core_terms = [
        "law", "legal", "ipc", "bnss", "bns", "crpc", "section", "complaint", "fir",
        "case", "rights", "lawyer", "advocate", "court", "bail", "arrest", "notice", "petition",
        "draft", "legal notice", "police complaint"
    ]

    legal_signal = has_any(legal_core_terms) or legal_category_detected or explicit_emergency

    if not legal_signal and not explicit_emergency and not accident_like and not cyber_fraud_like and not theft_or_crime_like:
        plan["intent"] = "general_query"
        plan["use_retrieval"] = False
        plan["use_case_search"] = False
        plan["use_lawyer_lookup"] = False
        plan["use_emergency"] = False
        plan["use_draft_generator"] = False

    # ------------------ NORMALIZE INTENT ------------------
    intent = plan.get("intent", "legal_query")
    if isinstance(intent, str):
        intent = intent.lower().strip()
    else:
        intent = "legal_query"

    # ------------------ LOCATION EXTRACTION ------------------
    location = plan.get("location")

    if not location:
        match = re.search(r"(?:in|from|at)\s+([A-Za-z\s]+)", query, re.IGNORECASE)
        if match:
            location = match.group(1).strip()

    if isinstance(location, str):
        location = location.strip().rstrip(".,") or None

    # ------------------ INCIDENT DESCRIPTION ------------------
    incident_description = query

    # ------------------ CATEGORY CLASSIFICATION ------------------
    category = "General"

    category_priority = [
        "Women Safety",
        "Violence",
        "Traffic",
        "Fraud",
        "Cyber Crime",
        "Property",
        "Public Order",
        "Police Misuse",
        "Defamation",
    ]

    for candidate in category_priority:
        if candidate in matched_categories:
            category = candidate
            break

    # ------------------ UPDATE STATE ------------------
    state["plan"] = plan
    state["intent"] = intent
    state["location"] = location
    state["incident_description"] = incident_description
    state["category"] = category

    # ------------------ DEBUG LOGGING ------------------
    print("\n=== PLANNER DEBUG ===")
    print("Query:", query)
    print("Intent:", intent)
    print("Plan:", plan)
    print("Location:", location)
    print("Category:", category)
    print("=====================\n")

    return state