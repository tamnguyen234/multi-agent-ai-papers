import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.models.paper import Paper
from app.db.models.topic import Topic, PaperTopic
from app.core.config import settings

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
            "summary": paper.summary_en or ""
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
        
    # 2. Call local Trend Agent model directly
    from app.services.trend_model.services import pipeline_service
    
    # --- MOCK LLM FIX ---
    # Patch requests.post to fix model hallucination and switch to llama3.2:1b
    original_post = pipeline_service.requests.post
    def patched_post(url, json=None, **kwargs):
        if url == "http://localhost:11434/api/generate" and json:
            json["model"] = "llama3.2:1b"
            # Prevent infinite token generation loops
            json["options"] = {"num_predict": 10, "stop": ["\n", ".", ","]}
        return original_post(url, json=json, **kwargs)
    pipeline_service.requests.post = patched_post
    # --------------------

    process_topic_clustering = pipeline_service.process_topic_clustering
    generate_embeddings = pipeline_service.generate_embeddings
    # -----------------------------------------------------
    
    
    class PaperMock:
        def __init__(self, id, title, abstract, published):
            self.id = id
            self.title = title
            self.abstract = abstract
            self.published = published
            self.paper_vector = None
            self.umap_x = None
            self.umap_y = None

    mock_papers = [
        PaperMock(id=p.id, title=p.title, abstract=p.abstract, published=p.published)
        for p in papers
    ]
    
    # Generate embeddings
    texts_to_process = [f"{p.title}. {p.abstract}" for p in mock_papers]
    vectors = generate_embeddings(texts_to_process)
    for i, p in enumerate(mock_papers):
        p.paper_vector = vectors[i].tolist()
        
    # Process clustering
    graph = process_topic_clustering(None, mock_papers)
    
    # Reconstruct topics from graph nodes
    topics_map = {}
    for node in graph["nodes"]:
        topics_map[node["id"]] = {
            "name": node["name"],
            "description": "Keywords: " + ", ".join(node["keywords"]),
            "paper_ids": [],
            "confidence_score": 0.85 # Default confidence since pipeline_service doesn't return one
        }
    
    for mp in mock_papers:
        if mp.umap_x is not None and mp.umap_y is not None:
            closest_node_id = None
            min_dist = float('inf')
            for node in graph.get("nodes", []):
                dist = math.sqrt((mp.umap_x - node["x"])**2 + (mp.umap_y - node["y"])**2)
                if dist < min_dist:
                    min_dist = dist
                    closest_node_id = node["id"]
            
            if closest_node_id is not None:
                topics_map[closest_node_id]["paper_ids"].append(mp.id)
                
    final_topics = [t for t in topics_map.values() if len(t["paper_ids"]) > 0]
    
    agent_res = {
        "mode": getattr(settings, "TREND_MODE", "rule_based"),
        "topics": final_topics
    }
    
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
