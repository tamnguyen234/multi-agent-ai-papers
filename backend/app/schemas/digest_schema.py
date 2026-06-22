from pydantic import BaseModel, model_validator
from datetime import date
from typing import List, Optional
from app.schemas.paper_schema import verify_audio_path_exists

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

    @model_validator(mode="after")
    def verify_audio_exists(self) -> "DigestPaperPaperResponse":
        if self.has_audio:
            if not verify_audio_path_exists(self.has_audio, self.audio_abstract_path):
                self.has_audio = False
                self.audio_abstract_path = None
                self.audio_abstract_url = None
                self.audio_duration_seconds = None
        return self


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
