from __future__ import annotations
from datetime import date
from typing import Any, Optional, List
from pydantic import BaseModel


class HFDailyPaper(BaseModel):
    rank_position: Optional[int] = None
    external_id: str
    title: str
    abstract_en: str
    authors: List[str] = []
    published: Optional[date] = None
    source_url: str
    upvotes: int = 0
    score: float = 0.0


class TranslationResult(BaseModel):
    translated_text: str
    mode: Optional[str] = None
    fallback_reason: Optional[str] = None


class TTSResult(BaseModel):
    audio_base64: str
    mime_type: str
    file_extension: str
    duration_seconds: Optional[float] = None
    timestamps: Any = None
    mode: Optional[str] = None
    fallback_reason: Optional[str] = None


class StoredAudio(BaseModel):
    file_path: str
    audio_url: str
    duration_seconds: Optional[int] = None
    timestamps: Any = None


class PipelinePaperResult(BaseModel):
    paper_id: int
    external_id: str
    rank_position: int
    title: str
    abstract_en: str
    abstract_vi: Optional[str] = None
    audio_path: Optional[str] = None
    audio_url: Optional[str] = None


class DailyPipelineResult(BaseModel):
    digest_id: int
    digest_date: date
    total_papers: int
    papers: List[PipelinePaperResult]

