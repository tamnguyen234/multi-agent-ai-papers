import requests
import re
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

def fetch_arxiv_papers(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch recent papers from HuggingFace Daily Papers instead of arXiv.
    If today is Saturday or Sunday, fetch papers from Friday.
    """
    logger.info("Fetching papers from HuggingFace Daily Papers API...")
    url = "https://huggingface.co/api/daily_papers"
    
    from datetime import timedelta
    now = datetime.now()
    weekday = now.weekday()
    
    params = {"limit": 50}
    if weekday in (5, 6):
        logger.info("Today is weekend. Requesting latest papers from Daily Papers (no date filter).")
        
    try:
        # Fetch a larger pool to allow sorting/filtering
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            logger.error(f"Failed to query HuggingFace API: {response.status_code}")
            return []
        
        results = response.json()
    except Exception as e:
        logger.error(f"HuggingFace Daily Papers API query failed: {str(e)}", exc_info=True)
        return []
        
    unique_papers = []
    seen_ids = set()
    
    for item in results:
        paper = item.get("paper")
        if not paper:
            continue
            
        clean_id = paper.get("id")
        if not clean_id or clean_id in seen_ids:
            continue
        seen_ids.add(clean_id)
        
        title = paper.get("title", "").replace('\n', ' ').strip()
        title = re.sub(r'\s+', ' ', title)
        
        abstract = paper.get("summary", "").replace('\n', ' ').strip()
        abstract = re.sub(r'\s+', ' ', abstract)
        
        authors = [a.get("name", "") for a in paper.get("authors", [])]
        
        # parse published date
        pub_str = paper.get("publishedAt", "")
        if pub_str:
            try:
                # e.g., '2026-06-18T00:00:00.000Z'
                published_dt = datetime.strptime(pub_str[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
            except ValueError:
                published_dt = datetime.now(timezone.utc)
        else:
            published_dt = datetime.now(timezone.utc)
            
        published_str = published_dt.strftime("%Y-%m-%d")
        
        unique_papers.append({
            "arxiv_id": clean_id,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "published": published_str,
            "published_dt": published_dt,
            "pdf_url": f"https://arxiv.org/pdf/{clean_id}.pdf",
            "categories": ["cs.AI"],
            "primary_category": "cs.AI",
            "entry_url": f"https://arxiv.org/abs/{clean_id}",
            "updated": published_str,
            "upvotes": paper.get("upvotes", 0)
        })
    
    # Sort by upvotes descending as a primary signal of quality
    unique_papers.sort(key=lambda p: p.get("upvotes", 0), reverse=True)
    
    logger.info(f"Successfully retrieved and parsed {len(unique_papers)} papers from HuggingFace.")
    return unique_papers[:limit]

