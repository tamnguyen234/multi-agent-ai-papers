from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class TrendPaperItem(BaseModel):
    id: int
    title: str
    abstract: str
    published: Optional[date] = None

    class Config:
        from_attributes = True

class TrendTopicResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    keywords: List[str] = []
    paper_count: int
    confidence_avg: float
    papers: List[TrendPaperItem] = []

    class Config:
        from_attributes = True

class TrendAnalyzeResponse(BaseModel):
    mode: str
    total_papers: int
    topic_count: int
    topics: List[TrendTopicResponse] = []

    class Config:
        from_attributes = True
