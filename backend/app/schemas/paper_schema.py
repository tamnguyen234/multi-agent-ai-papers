from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional, Any

class AudioAbstractResponse(BaseModel):
    id: int
    file_path: str
    audio_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    paper_timestamps: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AudioAbstractRequest(BaseModel):
    voice: Optional[str] = "vi_female"
    language: Optional[str] = "vi"
    force: Optional[bool] = False

class LazyAudioAbstractResponse(BaseModel):
    mode: str  # "existing" | "generated"
    audio_url: str
    duration_seconds: Optional[int] = None
    voice: Optional[str] = None
    language: Optional[str] = None
    audio_abstract: Optional[AudioAbstractResponse] = None
    error: Optional[str] = None


class PaperResponse(BaseModel):
    id: int
    external_id: str
    title: str
    abstract: str
    summary_en: Optional[str] = None
    summary_vi: Optional[str] = None
    source_url: Optional[str] = None
    authors: Optional[List[str]] = None
    published: Optional[date] = None
    pdf_path: Optional[str] = None
    pdf_url: Optional[str] = None
    score: float
    has_audio: bool
    created_at: datetime
    audio_abstract: Optional[AudioAbstractResponse] = None
    audio_abstract_path: Optional[str] = None
    audio_abstract_url: Optional[str] = None
    audio_duration_seconds: Optional[float] = None

    class Config:
        from_attributes = True
