from sqlalchemy import Column, BigInteger, String, Text, DateTime, Float, ForeignKey, UniqueConstraint, CheckConstraint, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Topic(Base):
    __tablename__ = "topics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    keywords_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    # Relationships
    paper_topics = relationship("PaperTopic", back_populates="topic", cascade="all, delete-orphan")

class PaperTopic(Base):
    __tablename__ = "paper_topics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    paper_id = Column(BigInteger, ForeignKey("papers.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    topic_id = Column(BigInteger, ForeignKey("topics.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    confidence_score = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    paper = relationship("Paper", back_populates="paper_topics")
    topic = relationship("Topic", back_populates="paper_topics")

    # Constraints
    __table_args__ = (
        UniqueConstraint("paper_id", "topic_id", name="uq_paper_topic"),
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="chk_confidence_score"),
    )
