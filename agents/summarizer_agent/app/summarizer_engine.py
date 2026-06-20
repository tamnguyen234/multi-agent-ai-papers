import logging
from datetime import datetime
from typing import List, Tuple, Optional
from app.config import settings
from app.schemas import PaperItem
from app.mock_summarizer import get_mock_papers
from app.arxiv_client import fetch_arxiv_papers
from app.scoring import score_and_select_top5
from app.summarization import generate_extractive_summary

logger = logging.getLogger(__name__)

def summarize_daily_top5_engine(mode_override: Optional[str] = None) -> Tuple[List[PaperItem], str, Optional[str]]:
    """
    Orchestrate daily top 5 papers generation.
    Supports mock, real, and mock_fallback modes.
    Ensures safe recovery on network/API failure and always returns exactly 5 papers in fallback mode.
    """
    env_mode = settings.SUMMARIZER_MODE
    mode = mode_override.lower().strip() if mode_override else env_mode
    
    allowed_modes = ["mock", "real", "mock_fallback"]
    if mode not in allowed_modes:
        raise ValueError(f"Invalid mode '{mode}'. Allowed modes are: {', '.join(allowed_modes)}")
        
    today_str = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"Summarizer Agent starting. Mode: {mode}, Date: {today_str}")
    
    if mode == "mock":
        return get_mock_papers(today_str), "mock", None
        
    elif mode == "real":
        # Force real mode: fetch from arXiv and fail on error or insufficient data
        raw_papers = fetch_arxiv_papers(limit=5)
        if len(raw_papers) < 5:
            raise ValueError(f"arXiv query returned only {len(raw_papers)} papers, expected at least 5 in 'real' mode.")
            
        top_papers = score_and_select_top5(raw_papers, limit=5)
        
        final_papers = []
        for p in top_papers:
            summary = generate_extractive_summary(p["abstract"])
            final_papers.append(PaperItem(
                rank_position=p["rank_position"],
                arxiv_id=p["arxiv_id"],
                title=p["title"],
                abstract=p["abstract"],
                summary=summary,
                authors=p["authors"],
                published=p["published"],
                pdf_url=p["pdf_url"],
                pdf_path=p.get("pdf_path"),
                score=p["score"],
                categories=p.get("categories"),
                primary_category=p.get("primary_category"),
                entry_url=p.get("entry_url"),
                updated=p.get("updated")
            ))
        return final_papers, "real", None
        
    else:  # mock_fallback
        try:
            raw_papers = fetch_arxiv_papers(limit=5)
            
            if not raw_papers:
                # Fallback to all mock papers if absolutely nothing is returned
                logger.warning("No papers fetched from arXiv. Falling back completely to mock papers.")
                return get_mock_papers(today_str), "mock_fallback", "arXiv query returned no results. Fell back to mock papers."
                
            top_papers = score_and_select_top5(raw_papers, limit=5)
            k = len(top_papers)
            
            if k >= 5:
                # Fully successful real path
                final_papers = []
                for p in top_papers:
                    summary = generate_extractive_summary(p["abstract"])
                    final_papers.append(PaperItem(
                        rank_position=p["rank_position"],
                        arxiv_id=p["arxiv_id"],
                        title=p["title"],
                        abstract=p["abstract"],
                        summary=summary,
                        authors=p["authors"],
                        published=p["published"],
                        pdf_url=p["pdf_url"],
                        pdf_path=p.get("pdf_path"),
                        score=p["score"],
                        categories=p.get("categories"),
                        primary_category=p.get("primary_category"),
                        entry_url=p.get("entry_url"),
                        updated=p.get("updated")
                    ))
                return final_papers, "real", None
            else:
                # Partially successful (K < 5): fill remaining (5 - K) with mock papers
                logger.warning(f"Only found {k} real papers on arXiv. Filling remaining {5-k} with mock papers.")
                fallback_reason = f"Only found {k} real papers on arXiv. Filled the remaining {5-k} with mock papers."
                
                final_papers = []
                for p in top_papers:
                    summary = generate_extractive_summary(p["abstract"])
                    final_papers.append(PaperItem(
                        rank_position=p["rank_position"],
                        arxiv_id=p["arxiv_id"],
                        title=p["title"],
                        abstract=p["abstract"],
                        summary=summary,
                        authors=p["authors"],
                        published=p["published"],
                        pdf_url=p["pdf_url"],
                        pdf_path=p.get("pdf_path"),
                        score=p["score"],
                        categories=p.get("categories"),
                        primary_category=p.get("primary_category"),
                        entry_url=p.get("entry_url"),
                        updated=p.get("updated")
                    ))
                    
                mock_list = get_mock_papers(today_str)
                needed = 5 - k
                for idx, mock_paper in enumerate(mock_list[:needed]):
                    mock_paper.rank_position = k + idx + 1
                    final_papers.append(mock_paper)
                    
                return final_papers, "mock_fallback", fallback_reason
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Summarizer Agent RAG/arXiv pipeline failed. Falling back. Reason: {error_msg}")
            return get_mock_papers(today_str), "mock_fallback", f"arXiv pipeline error: {error_msg}. Fell back to mock papers."
