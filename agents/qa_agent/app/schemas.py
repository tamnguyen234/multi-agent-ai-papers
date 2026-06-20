from pydantic import BaseModel, Field
from typing import Optional, List, Any

class QAAskRequest(BaseModel):
    paper_id: int
    pdf_path: Optional[str] = None
    title: Optional[str] = None
    abstract: Optional[str] = None
    summary: Optional[str] = None
    question: str
    mode: Optional[str] = None
    arxiv_id: Optional[str] = None

class QASource(BaseModel):
    page: int
    chunk_id: str
    text: str
    score: float

class QAAskResponse(BaseModel):
    answer: str
    sources: Optional[List[QASource]] = []
    mode: str
    fallback_reason: Optional[str] = None
    error: Optional[str] = None
