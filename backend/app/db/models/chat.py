from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey, JSON, Enum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    paper_id = Column(BigInteger, ForeignKey("papers.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    paper = relationship("Paper", back_populates="chat_sessions")
    chat_messages = relationship("ChatMessage", back_populates="chat_session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chat_session_id = Column(BigInteger, ForeignKey("chat_sessions.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    role = Column(Enum('user', 'assistant', 'system', name='chat_message_role_enum'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    # Relationships
    chat_session = relationship("ChatSession", back_populates="chat_messages")

    @property
    def session_id(self) -> int:
        return self.chat_session_id

    @session_id.setter
    def session_id(self, value: int):
        self.chat_session_id = value
