
from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import logging
from sqlalchemy.exc import SQLAlchemyError
from app.core.graph.builder import build_graph
from app.core.observability.langsmith_config import (
	is_langsmith_enabled,
	build_langsmith_run_config,
)
from app.db.postgres.queries import save_chat, get_chat_history, get_all_sessions, delete_chat_session
from app.db.postgres.connection import get_db
import uuid
from langsmith import traceable

router = APIRouter()
logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
	query: str
	session_id: str = None


# Initialize the graph once
graph = build_graph()

@router.post("/query")
@traceable(name="query_endpoint", run_type="chain")
async def query_endpoint(
	request: QueryRequest,
	response_format: str = Query("json", pattern="^(json|text)$"),
	db=Depends(get_db)
):
	user_query = request.query
	session_id = getattr(request, "session_id", None) or str(uuid.uuid4())
	try:
		history = get_chat_history(db, session_id, limit=4)
	except SQLAlchemyError as exc:
		logger.warning("Failed to fetch prior chat history for session %s: %s", session_id, exc)
		history = []
	prior_queries = [item.get("query", "") for item in reversed(history) if item.get("query")]
	conversation_context = "\n".join(prior_queries)
	graph_input = {
		"query": user_query,
		"session_id": session_id,
		"conversation_context": conversation_context,
	}
	graph_config = build_langsmith_run_config(
		run_name="nyaya_saathi_query",
		session_id=session_id,
		response_format=response_format,
		query=user_query,
		route="query",
	)

	if is_langsmith_enabled():
		result = graph.invoke(graph_input, config=graph_config)
	else:
		result = graph.invoke(graph_input)
	try:
		save_chat(db, session_id, user_query, result)
	except SQLAlchemyError as exc:
		# Do not fail user response if chat persistence is temporarily unavailable.
		logger.warning("Failed to persist chat for session %s: %s", session_id, exc)

	# Always return the structured answer payload, never the raw graph state.
	answer = result.get("answer", result) if isinstance(result, dict) else result

	# Optional plain-text mode for draft output where actual line breaks are preferred.
	if response_format == "text" and isinstance(answer, dict):
		draft = answer.get("draft")
		if isinstance(draft, dict):
			content = draft.get("content")
			if isinstance(content, str):
				return PlainTextResponse(content)

	if isinstance(answer, dict):
		return answer

	return {"result": answer}


@router.get("/sessions")
async def get_sessions(limit: int = Query(50, ge=1, le=100), db=Depends(get_db)):
	"""Get all session IDs with their most recent timestamps."""
	try:
		sessions = get_all_sessions(db, limit=limit)
		return [{"session_id": session[0], "timestamp": session[1]} for session in sessions]
	except SQLAlchemyError as exc:
		logger.warning("Failed to fetch sessions: %s", exc)
		return []


@router.get("/history/{session_id}")
async def get_history(session_id: str, limit: int = Query(50, ge=1, le=100), db=Depends(get_db)):
	"""Get chat history for a specific session."""
	try:
		history = get_chat_history(db, session_id, limit=limit)
		return {"session_id": session_id, "chats": history}
	except SQLAlchemyError as exc:
		logger.warning("Failed to fetch history for session %s: %s", session_id, exc)
		return {"session_id": session_id, "chats": []}


@router.delete("/history/{session_id}")
async def delete_history(session_id: str, db=Depends(get_db)):
	"""Delete all chat history for a specific session."""
	try:
		deleted_count = delete_chat_session(db, session_id)
		return {"session_id": session_id, "deleted": deleted_count}
	except SQLAlchemyError as exc:
		logger.warning("Failed to delete history for session %s: %s", session_id, exc)
		return {"session_id": session_id, "deleted": 0}
