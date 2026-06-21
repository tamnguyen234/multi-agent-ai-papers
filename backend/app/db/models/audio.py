from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import Optional
from app.db.database import Base

class AudioAbstract(Base):
    __tablename__ = "audio_abstracts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    paper_id = Column(BigInteger, ForeignKey("papers.id", ondelete="CASCADE", onupdate="CASCADE"), unique=True, nullable=False)
    file_path = Column(String(500), nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    paper_timestamps = Column("paper_timestamps", JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    paper = relationship("Paper", back_populates="audio_abstract")



    @property
    def audio_url(self) -> Optional[str]:
        if self.file_path:
            return "/static/" + self.file_path.lstrip("/")
        return None
