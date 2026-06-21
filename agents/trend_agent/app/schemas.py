from pydantic import BaseModel
from typing import List, Optional, Dict

class PaperItem(BaseModel):
    id: int
    title: str
    abstract: Optional[str] = None
    summary: Optional[str] = None
    published: Optional[str] = None

class AnalyzeRequest(BaseModel):
    papers: List[PaperItem]
    mode: Optional[str] = None

class TopicResponseItem(BaseModel):
    name: str
    description: str
    keywords: List[str]
    paper_ids: List[int]
    paper_scores: Optional[Dict[str, float]] = None
    confidence_score: float

class AnalyzeResponse(BaseModel):
    mode: str
    total_papers: int
    topics: List[TopicResponseItem]
    fallback_reason: Optional[str] = None
