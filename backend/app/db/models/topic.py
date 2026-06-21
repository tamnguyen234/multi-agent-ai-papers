from sqlalchemy import Column, BigInteger, String, Text, DateTime, Float, ForeignKey, UniqueConstraint, CheckConstraint, JSON, Integer, Date
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

class TrendRun(Base):
    __tablename__ = "trend_runs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    window_days = Column(Integer, default=30, nullable=False)
    date_from = Column(Date, nullable=True)
    date_to = Column(Date, nullable=True)
    paper_count = Column(Integer, default=0, nullable=False)
    mode = Column(String(100), nullable=True)
    status = Column(String(50), default="running", nullable=False)  # 'running', 'success', 'failed'
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, server_default=func.now(), nullable=False)
    finished_at = Column(DateTime, nullable=True)

    # Relationships
    paper_topics = relationship("PaperTopic", back_populates="trend_run")

class PaperTopic(Base):
    __tablename__ = "paper_topics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    paper_id = Column(BigInteger, ForeignKey("papers.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    topic_id = Column(BigInteger, ForeignKey("topics.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    trend_run_id = Column(BigInteger, ForeignKey("trend_runs.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True, index=True)
    confidence_score = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    paper = relationship("Paper", back_populates="paper_topics")
    topic = relationship("Topic", back_populates="paper_topics")
    trend_run = relationship("TrendRun", back_populates="paper_topics")

    # Constraints
    __table_args__ = (
        UniqueConstraint("paper_id", "topic_id", name="uq_paper_topic"),
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="chk_confidence_score"),
    )
