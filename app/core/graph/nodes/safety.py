from langsmith import traceable


@traceable(name="safety_node", run_type="chain")
def safety_node(state: dict) -> dict:
    """
    Applies legal disclaimer only for legal_query and draft_generator intents.
    Removes disclaimer for other intents.
    """
    disclaimer_text = "This is not legal advice. Please consult a qualified lawyer."
    allowed_intents = {"legal_query", "draft_generator"}
    intent = (state.get("intent") or "").lower()
    answer = state.get("answer", {})

    if isinstance(answer, dict):
        if intent in allowed_intents:
            if "disclaimer" not in answer:
                answer["disclaimer"] = disclaimer_text
        else:
            answer.pop("disclaimer", None)
        state["answer"] = answer

    return state
