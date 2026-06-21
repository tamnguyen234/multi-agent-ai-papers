from pydantic import BaseModel
from typing import List, Optional

class PaperItem(BaseModel):
    rank_position: int
    arxiv_id: str
    title: str
    abstract: str
    summary: str
    authors: List[str]
    published: str
    pdf_url: str
    pdf_path: Optional[str] = None
    score: float
    upvotes: int = 0
    categories: Optional[List[str]] = None
    primary_category: Optional[str] = None
    entry_url: Optional[str] = None
    updated: Optional[str] = None

class DailyTop5Request(BaseModel):
    date: Optional[str] = None
    mode: Optional[str] = None
    limit: Optional[int] = 5

class DailyTop5Response(BaseModel):
    date: str
    mode: str
    fallback_reason: Optional[str] = None
    papers: List[PaperItem]
