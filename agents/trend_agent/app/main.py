from fastapi import FastAPI, HTTPException, status
import logging
import importlib.util
from app.config import settings
from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.embeddings import EmbeddingEngine
from app.trend_engine import analyze_trends_engine

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trend_agent")

app = FastAPI(
    title="Trend Agent",
    description="Agent for analyzing topic trends and clusters among research papers using BERTopic and rule-based fallback.",
    version="0.2.0"
)

@app.get("/")
def root():
    return {"message": "Trend Agent is running"}

@app.get("/health")
def health_check():
    """
    Return health check status.
    Must not trigger loading embedding models or heavy components.
    """
    # Use find_spec to check package availability without importing them
    bertopic_available = importlib.util.find_spec("bertopic") is not None
    
    return {
        "status": "ok",
        "service": "trend_agent",
        "mode": settings.TREND_MODE,
        "embedding_model_loaded": EmbeddingEngine.get_instance().is_loaded(),
        "bertopic_available": bertopic_available
    }

@app.post("/trend/analyze", response_model=AnalyzeResponse)
def analyze_trends(payload: AnalyzeRequest):
    """
    Cluster and categorize a list of papers into topics.
    Dynamically routes to BERTopic or rule-based matching depending on requested/configured mode.
    """
    if not isinstance(payload.papers, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload field 'papers' must be a list."
        )
        
    if not payload.papers:
        return AnalyzeResponse(
            mode=payload.mode or settings.TREND_MODE,
            total_papers=0,
            topics=[]
        )
        
    try:
        topics, mode, fallback_reason = analyze_trends_engine(payload.papers, payload.mode)
        return AnalyzeResponse(
            mode=mode,
            total_papers=len(payload.papers),
            topics=topics,
            fallback_reason=fallback_reason
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Trend analyze endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trend analysis failed: {str(e)}"
        )
