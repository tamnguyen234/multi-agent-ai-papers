import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

CATEGORY_WEIGHTS = {
    "cs.AI": 1.0,   # Artificial Intelligence
    "cs.CL": 1.0,   # Computation and Language (NLP)
    "cs.LG": 1.0,   # Machine Learning
    "cs.CV": 0.8,   # Computer Vision
    "cs.RO": 0.7,   # Robotics
    "cs.SD": 0.7    # Sound/Speech
}

TRENDING_KEYWORDS = [
    "llm", "large language model", "transformer", "prompt", "gpt", "llama", "deepseek", "qwen",
    "rag", "retrieval", "vector database", "embedding", "faiss", "document qa",
    "agent", "multi-agent", "autonomous agent", "workflow", "coordination",
    "safety", "alignment", "hallucination", "bias", "robustness", "trustworthy",
    "reasoning", "chain of thought", "mathematical",
    "diffusion", "image generation", "computer vision",
    "speech", "audio", "tts", "text-to-speech", "whisper",
    "robot", "robotics"
]

def score_and_select_top5(papers: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    """
    Apply a deterministic heuristic scoring algorithm to rank arXiv papers.
    Ranks papers based on recency, category weights, keyword matches, and cross-category boosts.
    Uses arxiv_id as a stable tie-breaker.
    """
    now = datetime.now(timezone.utc)
    
    scored_papers = []
    for paper in papers:
        # 1. Recency Score (0.0 to 1.0)
        # 1.0 for today, 0.5 for 1 day ago, 0.33 for 2 days ago, etc.
        published_dt = paper["published_dt"]
        age_days = (now - published_dt).total_seconds() / 86400.0
        recency_score = 1.0 / (1.0 + max(0.0, age_days))
        
        # 2. Category Weight (0.5 to 1.0)
        primary_cat = paper.get("primary_category", "")
        cat_weight = CATEGORY_WEIGHTS.get(primary_cat, 0.5)
        
        # 3. Keyword Boost (up to 0.3)
        text = f"{paper['title']} {paper['abstract']}".lower()
        keyword_matches = sum(1 for kw in TRENDING_KEYWORDS if kw in text)
        keyword_boost = min(0.3, keyword_matches * 0.05)
        
        # 4. Multi-Category Boost (0.05)
        all_cats = paper.get("categories", [])
        multi_cat_boost = 0.05 if len(all_cats) > 1 else 0.0
        
        # Calculate final heuristic score (ranges from ~0.15 to 0.99)
        final_score = (recency_score * 0.4) + (cat_weight * 0.3) + keyword_boost + multi_cat_boost
        final_score = round(min(0.99, max(0.10, final_score)), 2)
        
        # Attach score
        paper_copy = paper.copy()
        paper_copy["score"] = final_score
        scored_papers.append(paper_copy)
        
    # Sort deterministically:
    # 1. Score descending
    # 2. Published date descending (newest first)
    # 3. Arxiv ID descending (stable tie-breaker)
    sorted_papers = sorted(
        scored_papers,
        key=lambda p: (p["score"], p["published_dt"], p["arxiv_id"]),
        reverse=True
    )
    
    # Select top 5
    top_papers = sorted_papers[:limit]
    
    # Assign rank_position 1..limit
    for rank, paper in enumerate(top_papers, 1):
        paper["rank_position"] = rank
        # Clean up published_dt helper from final return payload
        if "published_dt" in paper:
            del paper["published_dt"]
            
    logger.info(f"Selected top {len(top_papers)} papers using trending score.")
    return top_papers
