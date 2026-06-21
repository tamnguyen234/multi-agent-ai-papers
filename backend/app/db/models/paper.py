from sqlalchemy import Column, BigInteger, String, Text, Date, DateTime, Boolean, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import Optional
from app.db.database import Base

class Paper(Base):
    __tablename__ = "papers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    external_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    abstract_en = Column(Text, nullable=False)
    abstract_vi = Column(Text, nullable=True)
    authors = Column("authors", JSON, nullable=True)
    published = Column(Date, nullable=True, index=True)
    source_url = Column(Text, nullable=True)
    pdf_path = Column(String(500), nullable=True)
    source = Column(String(100), nullable=False)
    score = Column("score", Float, nullable=False, default=0, index=True)
    has_audio = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)




    # Relationships
    digest_papers = relationship("DigestPaper", back_populates="paper", cascade="all, delete-orphan")
    audio_abstract = relationship("AudioAbstract", back_populates="paper", uselist=False, cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="paper", cascade="all, delete-orphan")
    paper_topics = relationship("PaperTopic", back_populates="paper", cascade="all, delete-orphan")

    @property
    def audio_abstract_path(self) -> Optional[str]:
        if self.audio_abstract:
            return self.audio_abstract.file_path
        return None

    @property
    def audio_abstract_url(self) -> Optional[str]:
        if self.audio_abstract and self.audio_abstract.file_path:
            return "/static/" + self.audio_abstract.file_path.lstrip("/")
        return None

    @property
    def audio_duration_seconds(self) -> Optional[float]:
        if self.audio_abstract:
            return self.audio_abstract.duration_seconds
        return None

    @property
    def pdf_url(self) -> Optional[str]:
        if not self.pdf_path:
            return None
        path_str = self.pdf_path.lstrip("/")
        if path_str.startswith("data/"):
            return "/static/" + path_str
        else:
            return "/static/data/" + path_str


