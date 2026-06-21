from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class DigestPaperPaperResponse(BaseModel):
    id: int
    external_id: str
    title: str
    abstract_en: str
    abstract_vi: Optional[str] = None
    authors: Optional[List[str]] = None
    score: float
    published: Optional[date] = None
    has_audio: bool
    audio_abstract_path: Optional[str] = None
    audio_abstract_url: Optional[str] = None
    audio_duration_seconds: Optional[float] = None

    class Config:
        from_attributes = True

class DigestPaperResponse(BaseModel):
    rank_position: int
    paper: DigestPaperPaperResponse

    class Config:
        from_attributes = True

class DigestResponse(BaseModel):
    id: int
    digest_date: date
    papers: List[DigestPaperResponse]

    class Config:
        from_attributes = True
