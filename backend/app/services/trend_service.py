import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.models.paper import Paper
from app.db.models.topic import Topic, PaperTopic
from app.core.config import settings
from app.services import trend_client

logger = logging.getLogger(__name__)

TOPIC_KEYWORDS = {
    "LLM": ["llm", "large language model", "language model", "transformer", "prompt", "prompting", "generative ai", "gpt", "llama", "instruction tuning"],
    "RAG": ["rag", "retrieval augmented generation", "retrieval", "vector database", "embedding", "faiss", "knowledge base", "document qa", "citation"],
    "Multi-Agent": ["agent", "multi-agent", "autonomous agent", "tool use", "planning", "orchestration", "workflow", "coordination"],
    "Computer Vision": ["computer vision", "image", "vision", "object detection", "segmentation", "diffusion", "video", "multimodal", "clip"],
    "Speech / Audio": ["speech", "audio", "tts", "text-to-speech", "asr", "voice", "speaker", "waveform"],
    "Reinforcement Learning": ["reinforcement learning", "rl", "reward", "policy", "agent environment", "q-learning", "decision making"],
    "AI Safety": ["safety", "alignment", "hallucination", "bias", "robustness", "evaluation", "red teaming", "trustworthy"],
    "AI Systems": ["serving", "inference", "optimization", "latency", "distributed", "deployment", "hardware", "gpu", "efficiency"],
    "Other": []
}

class TrendService:
    def __init__(self, db: Session):
        self.db = db

    def analyze_trends(self, limit: int | None = None):
        """Call Trend Agent to cluster and identify main topics/trends in saved papers."""
        return analyze_and_store_trends(self.db, limit)

def build_paper_payload(papers: list[Paper]) -> list[dict]:
    """Convert Paper model list to serialized dict payload for Trend Agent."""
    payload = []
    for paper in papers:
        payload.append({
            "id": paper.id,
            "title": paper.title,
            "abstract": paper.abstract or "",
            "summary": paper.summary or ""
        })
    return payload

def analyze_and_store_trends(db: Session, limit: int | None = None) -> dict:
    """
    Fetch papers, invoke the Trend Agent microservice, upsert topics & paper mappings,
    and return the serialized trend report.
    """
    # 1. Fetch papers ordered by published date descending, fallback to created_at
    query = db.query(Paper).order_by(Paper.published.desc(), Paper.created_at.desc())
    if limit is not None:
        query = query.limit(limit)
    papers = query.all()
    
    if not papers:
        return {
            "mode": settings.TREND_MODE,
            "total_papers": 0,
            "topic_count": 0,
            "topics": []
        }
        
    # 2. Call Trend Agent
    payload = {
        "papers": build_paper_payload(papers),
        "mode": settings.TREND_MODE
    }
    
    agent_res = trend_client.analyze_trends(payload)
    
    # Track the successfully saved topics and confidence counts to return in API response
    processed_topics = []
    
    try:
        # Create map of paper_id -> Paper to check existence
        paper_map = {p.id: p for p in papers}
        
        for t_data in agent_res["topics"]:
            topic_name = t_data["name"]
            topic_desc = t_data["description"]
            paper_ids = t_data["paper_ids"]
            confidence = t_data["confidence_score"]
            
            # Filter paper_ids: skip those not existing in DB
            valid_paper_ids = []
            for pid in paper_ids:
                if pid in paper_map:
                    valid_paper_ids.append(pid)
                else:
                    # Try to fetch from DB in case it was not loaded in initial query
                    db_p = db.query(Paper).filter(Paper.id == pid).first()
                    if db_p:
                        valid_paper_ids.append(pid)
                        paper_map[pid] = db_p
                        
            if not valid_paper_ids:
                continue
                
            # Upsert Topic
            db_topic = db.query(Topic).filter(Topic.name == topic_name).first()
            if not db_topic:
                db_topic = Topic(name=topic_name, description=topic_desc)
                db.add(db_topic)
                db.flush()
            else:
                db_topic.description = topic_desc
                db.flush()
                
            # Upsert PaperTopic mappings
            for pid in valid_paper_ids:
                db_pt = db.query(PaperTopic).filter(
                    PaperTopic.paper_id == pid,
                    PaperTopic.topic_id == db_topic.id
                ).first()
                
                if not db_pt:
                    db_pt = PaperTopic(
                        paper_id=pid,
                        topic_id=db_topic.id,
                        confidence_score=confidence
                    )
                    db.add(db_pt)
                else:
                    db_pt.confidence_score = confidence
                    
            db.flush()
            
            # Save topic info for response building
            processed_topics.append({
                "id": db_topic.id,
                "name": db_topic.name,
                "description": db_topic.description,
                "keywords": TOPIC_KEYWORDS.get(db_topic.name, []),
                "paper_count": len(valid_paper_ids),
                "confidence_avg": confidence,
                "papers": [
                    {
                        "id": paper_map[pid].id,
                        "title": paper_map[pid].title,
                        "abstract": paper_map[pid].abstract,
                        "published": paper_map[pid].published
                    } for pid in valid_paper_ids
                ]
            })
            
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist trend analysis to database: {str(e)}"
        )
        
    # Sort topics by paper count descending
    processed_topics = sorted(processed_topics, key=lambda x: x["paper_count"], reverse=True)
    
    return {
        "mode": agent_res["mode"],
        "total_papers": len(papers),
        "topic_count": len(processed_topics),
        "topics": processed_topics
    }
