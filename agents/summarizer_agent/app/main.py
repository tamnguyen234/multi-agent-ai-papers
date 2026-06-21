from fastapi import FastAPI, HTTPException, status
import logging
from datetime import datetime
from typing import Optional

from app.config import settings
from app.schemas import DailyTop5Request, DailyTop5Response
from app.summarizer_engine import summarize_daily_top5_engine

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("summarizer_agent")

app = FastAPI(
    title="Summarizer Agent",
    description="Agent for fetching academic papers from arXiv, calculating trending scores, and summarizing abstracts.",
    version="0.2.0"
)

@app.get("/")
def root():
    return {"message": "Summarizer Agent is running"}

@app.get("/health")
def health_check():
    """
    Return health check status.
    Must remain extremely fast and NOT trigger any network requests (such as querying arXiv).
    """
    return {
        "status": "ok",
        "service": "summarizer_agent",
        "mode": settings.SUMMARIZER_MODE,
        "arxiv_enabled": True
    }

@app.post("/summarize/daily-top5", response_model=DailyTop5Response)
def daily_top5(payload: Optional[DailyTop5Request] = None):
    """
    Fetch and summarize the top 5 AI papers from arXiv.
    Supports mock, real, and mock_fallback modes.
    Always returns exactly 5 papers (with mock supplement if needed) in fallback mode.
    """
    mode_override = None
    if payload:
        mode_override = payload.mode
        
    try:
        papers, actual_mode, fallback_reason = summarize_daily_top5_engine(mode_override)
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        return DailyTop5Response(
            date=today_str,
            mode=actual_mode,
            fallback_reason=fallback_reason,
            papers=papers
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Daily top 5 summarizer failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarizer failed: {str(e)}"
        )
