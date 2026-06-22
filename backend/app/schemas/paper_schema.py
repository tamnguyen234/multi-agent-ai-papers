import os
from pydantic import BaseModel, Field, model_validator
from datetime import date, datetime
from typing import List, Optional, Any
from app.services.storage_service import get_project_root

def verify_audio_path_exists(has_audio: bool, path: Optional[str]) -> bool:
    if not has_audio or not path:
        return False
    try:
        project_root = get_project_root()
        disk_path = project_root / path.lstrip("/")
        return os.path.exists(disk_path) and os.path.getsize(disk_path) > 0
    except Exception:
        return False

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
    title: str = Field(..., description="Paper title")
    abstract_en: str = Field(..., description="Abstract in English")
    abstract_vi: Optional[str] = Field(None, description="Translated abstract in Vietnamese")
    source_url: Optional[str] = None
    authors: Optional[List[str]] = Field(None, description="List of authors")
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

    @model_validator(mode="after")
    def verify_audio_exists(self) -> "PaperResponse":
        if self.has_audio:
            path = None
            if self.audio_abstract and self.audio_abstract.file_path:
                path = self.audio_abstract.file_path
            elif self.audio_abstract_path:
                path = self.audio_abstract_path
            
            if not verify_audio_path_exists(self.has_audio, path):
                self.has_audio = False
                self.audio_abstract = None
                self.audio_abstract_path = None
                self.audio_abstract_url = None
                self.audio_duration_seconds = None
        return self

