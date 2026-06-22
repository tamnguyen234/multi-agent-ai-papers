from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.db.models.topic import Topic, PaperTopic
from app.db.models.paper import Paper
from app.core.config import settings
from app.schemas.trend_schema import TrendAnalyzeResponse
from app.services.trend_service import analyze_and_store_trends, TOPIC_KEYWORDS

router = APIRouter()

@router.get("/health")
def get_trend_health():
    """Verify Trend Model health (runs locally in backend)."""
    return {
        "status": "ok",
        "agent": {"message": "Trend Model is embedded locally"}
    }

@router.post("/analyze", response_model=TrendAnalyzeResponse)
def analyze_and_persist_trends(
    limit: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Trigger the Trend Agent to group saved papers and save the topics/mappings in database."""
    return analyze_and_store_trends(db, limit)

@router.get("/", response_model=TrendAnalyzeResponse)
def get_stored_trends(
    limit_topics: int = 20,
    limit_papers_per_topic: int = 10,
    db: Session = Depends(get_db)
):
    """Retrieve already computed trend clusters from database (does not query the Trend Agent)."""
    # 1. Fetch topics
    topics = db.query(Topic).limit(limit_topics).all()
    
    topics_list = []
    total_papers_set = set()
    
    for topic in topics:
        # Load mappings
        pts = db.query(PaperTopic).filter(PaperTopic.topic_id == topic.id).all()
        if not pts:
            continue
            
        paper_ids = [pt.paper_id for pt in pts]
        confidences = [pt.confidence_score for pt in pts]
        avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
        
        # Load actual paper details ordered by published desc, created_at desc
        papers = db.query(Paper).filter(Paper.id.in_(paper_ids))\
            .order_by(Paper.published.desc(), Paper.created_at.desc())\
            .limit(limit_papers_per_topic).all()
            
        for pid in paper_ids:
            total_papers_set.add(pid)
            
        topics_list.append({
            "id": topic.id,
            "name": topic.name,
            "description": topic.description,
            "keywords": TOPIC_KEYWORDS.get(topic.name, []),
            "paper_count": len(pts),
            "confidence_avg": avg_confidence,
            "papers": [
                {
                    "id": p.id,
                    "title": p.title,
                    "abstract": p.abstract_en,
                    "published": p.published
                } for p in papers
            ]
        })
        
    # Sort topics by paper_count descending
    topics_list = sorted(topics_list, key=lambda x: x["paper_count"], reverse=True)
    
    return {
        "mode": getattr(settings, "TREND_MODE", "rule_based"),
        "total_papers": len(total_papers_set),
        "topic_count": len(topics_list),
        "topics": topics_list
    }
