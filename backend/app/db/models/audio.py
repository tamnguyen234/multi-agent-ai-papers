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
    duration_seconds = Column(Float, nullable=True)
    voice = Column(String(100), nullable=True)
    language = Column(String(20), nullable=False, default="vi", server_default="vi")
    model_name = Column(String(255), nullable=True)
    paper_timestamps_json = Column("paper_timestamps_json", JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    # Relationships
    paper = relationship("Paper", back_populates="audio_abstract")

    @property
    def paper_timestamps(self):
        return self.paper_timestamps_json

    @paper_timestamps.setter
    def paper_timestamps(self, value):
        self.paper_timestamps_json = value

    @property
    def audio_url(self) -> Optional[str]:
        if self.file_path:
            return "/static/" + self.file_path.lstrip("/")
        return None
