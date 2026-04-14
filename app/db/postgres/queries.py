
import logging
from sqlalchemy import JSON, func
import json
from app.db.postgres.models import ChatHistory, Lawyer
from app.db.postgres.connection import SessionLocal

def get_lawyers_by_location(location: str, limit: int = 5):
    session = SessionLocal()
    try:
        loc = (location or "").strip()
        logging.info(f"[DEBUG] DB filter location: '{loc}', limit: {limit}")
        query = session.query(Lawyer)
        if loc:
            query = query.filter(Lawyer.location.ilike(f"%{loc}%"))
        if limit:
            query = query.limit(limit)
        results = query.all()
        logging.info(f"[DEBUG] DB raw results: {results}")
        lawyer_dicts = [
            {
                "name": lawyer.name,
                "specialization": lawyer.specialization,
                "location": lawyer.location,
                "contact": lawyer.contact
            }
            for lawyer in results
        ]
        logging.info(f"[DEBUG] Returning lawyer dicts: {lawyer_dicts}")
        return lawyer_dicts
    finally:
        session.close()

def save_chat(db, session_id: str, query: str, response):
    chat = ChatHistory(
        session_id=session_id,
        query=query,
        response=json.dumps(response)  # FIX
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat

def get_chat_history(db, session_id: str, limit: int = 5):
    results = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    formatted_results = []
    for chat in results:
        formatted_results.append(
            {
                "query": chat.query,
                "response": json.loads(chat.response),
                "timestamp": chat.created_at,
            }
        )
    return formatted_results

def get_all_sessions(db, limit: int = 50):
    """Get all unique session IDs with their most recent chat timestamp."""
    latest_created_at = func.max(ChatHistory.created_at).label("latest_created_at")
    results = (
        db.query(ChatHistory.session_id, latest_created_at)
        .group_by(ChatHistory.session_id)
        .order_by(latest_created_at.desc())
        .limit(limit)
        .all()
    )
    return results


def delete_chat_session(db, session_id: str) -> int:
    """Delete all chat rows for a given session. Returns number of deleted rows."""
    deleted = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return int(deleted)
