from datetime import date
from typing import Any
from pydantic import BaseModel


class HFDailyPaper(BaseModel):
    rank_position: int | None = None
    external_id: str
    title: str
    abstract_en: str
    authors: list[str] = []
    published: date | None = None
    source_url: str
    upvotes: int = 0
    score: float = 0.0



class TTSResult(BaseModel):
    audio_base64: str
    mime_type: str
    file_extension: str
    duration_seconds: float | None = None
    timestamps: Any = None
    mode: str | None = None
    fallback_reason: str | None = None


class StoredAudio(BaseModel):
    file_path: str
    audio_url: str
    duration_seconds: int | None = None
    timestamps: Any = None


class PipelinePaperResult(BaseModel):
    paper_id: int
    external_id: str
    rank_position: int
    title: str
    abstract_en: str
    abstract_vi: str | None
    audio_path: str | None
    audio_url: str | None


class DailyPipelineResult(BaseModel):
    digest_id: int
    digest_date: date
    total_papers: int
    papers: list[PipelinePaperResult]

