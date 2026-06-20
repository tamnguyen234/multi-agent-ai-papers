import arxiv
import re
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

def fetch_arxiv_papers(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch recent papers from arXiv for the configured AI categories.
    Implements dynamic days_back expansion to prevent missing data.
    """
    categories = settings.ARXIV_CATEGORIES
    # Join categories with OR operator
    query_parts = [f"cat:{cat}" for cat in categories]
    query_str = " OR ".join(query_parts)
    
    max_results = settings.ARXIV_MAX_RESULTS
    days_back = settings.ARXIV_DAYS_BACK
    
    logger.info(f"Querying arXiv with query: '{query_str}', max_results: {max_results}")
    
    client = arxiv.Client()
    search = arxiv.Search(
        query=query_str,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )
    
    try:
        results = list(client.results(search))
    except Exception as e:
        logger.error(f"Failed to query arXiv API: {str(e)}", exc_info=True)
        raise RuntimeError(f"arXiv API error: {str(e)}")
        
    if not results:
        return []
        
    # Deduplicate and normalize results
    seen_ids = set()
    unique_papers = []
    
    for r in results:
        raw_id = r.entry_id.split('/abs/')[-1]
        # Keep version if present, e.g. xxxx.xxxxxv2, as per user instructions
        clean_id = raw_id
        
        if clean_id in seen_ids:
            continue
        seen_ids.add(clean_id)
        
        # Normalize fields
        title = r.title.replace('\n', ' ').strip()
        # Replace multiple spaces with a single space
        title = re.sub(r'\s+', ' ', title)
        
        abstract = r.summary.replace('\n', ' ').strip()
        abstract = re.sub(r'\s+', ' ', abstract)
        
        authors = [author.name for author in r.authors]
        
        # Keep original timezone-aware datetime
        published_dt = r.published
        published_str = published_dt.strftime("%Y-%m-%d")
        
        # Build paper payload
        unique_papers.append({
            "arxiv_id": clean_id,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "published": published_str,
            "published_dt": published_dt,  # Keep dt for recency scoring
            "pdf_url": f"https://arxiv.org/pdf/{clean_id}.pdf",
            "categories": r.categories,
            "primary_category": r.primary_category,
            "entry_url": r.entry_id,
            "updated": r.updated.strftime("%Y-%m-%d") if r.updated else published_str
        })
        
    # Dynamic Days Back Filtering
    # Try filtering with default DAYS_BACK (e.g. 2 days)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days_back)
    recent_papers = [p for p in unique_papers if p["published_dt"] >= cutoff]
    
    if len(recent_papers) >= limit:
        logger.info(f"Found {len(recent_papers)} papers within last {days_back} days.")
        return recent_papers
        
    # Expand to 7 days if not enough
    logger.warning(f"Only found {len(recent_papers)} papers in last {days_back} days. Expanding to 7 days...")
    cutoff_7 = now - timedelta(days=7)
    recent_papers_7 = [p for p in unique_papers if p["published_dt"] >= cutoff_7]
    
    if len(recent_papers_7) >= limit:
        logger.info(f"Found {len(recent_papers_7)} papers within last 7 days.")
        return recent_papers_7
        
    # If still not enough, return all parsed unique papers without recency filter
    logger.warning(f"Found {len(recent_papers_7)} papers in last 7 days. Returning all latest {len(unique_papers)} papers.")
    return unique_papers
