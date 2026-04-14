from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.postgres.connection import Base


class Lawyer(Base):
	__tablename__ = "lawyers"

	id = Column(Integer, primary_key=True, index=True)
	name = Column(String, nullable=False)
	location = Column(String, nullable=False)
	specialization = Column(String, nullable=False)
	contact = Column(String, nullable=False)

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=False, index=True)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())