from fastapi import FastAPI, HTTPException, status
import logging
from app.schemas import QAAskRequest, QAAskResponse
from pydantic import BaseModel
from typing import Optional, List
from app.qa_engine import answer_question

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qa_agent")

app = FastAPI(
    title="Q&A Agent",
    description="Agent for chatting and querying AI research paper contents using Retrieval-Augmented Generation (RAG).",
    version="0.1.0"
)

# Preserve legacy schema models for /index and /query placeholders
class IndexRequest(BaseModel):
    paper_id: int
    pdf_path: str

class QueryRequest(BaseModel):
    paper_id: int
    question: str

@app.get("/")
def root():
    return {"message": "Q&A Agent is running"}

@app.get("/health")
def health_check():
    """
    Return health check status.
    Must not trigger loading embedding models or indices.
    """
    from app.embeddings import EmbeddingEngine
    from app.config import settings
    import httpx
    
    ollama_reachable = False
    ollama_error = None
    ollama_models = []
    
    url = f"{settings.QA_OLLAMA_BASE_URL.rstrip('/')}/api/tags"
    try:
        # Use short timeout of 1.5 seconds as requested
        response = httpx.get(url, timeout=1.5)
        if response.status_code == 200:
            ollama_reachable = True
            data = response.json()
            ollama_models = [m.get("name") for m in data.get("models", [])]
        else:
            ollama_error = f"Ollama returned status code {response.status_code}"
    except Exception as e:
        ollama_error = str(e)
        
    return {
        "status": "ok",
        "service": "qa_agent",
        "mode": settings.QA_MODE,
        "embedding_model_loaded": EmbeddingEngine.get_instance().is_loaded(),
        "llm_provider": settings.QA_LLM_PROVIDER,
        "ollama_base_url": settings.QA_OLLAMA_BASE_URL,
        "ollama_model": settings.QA_OLLAMA_MODEL,
        "ollama_reachable": ollama_reachable,
        "ollama_error": ollama_error,
        "ollama_models": ollama_models
    }

@app.post("/index")
def index_paper(payload: IndexRequest):
    """Placeholder endpoint to parse PDF and build FAISS index."""
    return {
        "status": "success",
        "message": f"Successfully indexed paper {payload.paper_id}"
    }

@app.post("/query")
def query_paper(payload: QueryRequest):
    """Placeholder endpoint to query paper content."""
    return {
        "status": "success",
        "answer": f"Mock reply to: '{payload.question}' regarding paper {payload.paper_id}",
        "sources": []
    }

@app.post("/qa/ask", response_model=QAAskResponse)
def qa_ask(payload: QAAskRequest):
    """Q&A endpoint to ask question about a paper (RAG mode)."""
    if not payload.question or not payload.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question must not be empty"
        )
        
    try:
        res = answer_question(payload)
        return QAAskResponse(**res)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"QA ask endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Q&A query failed: {str(e)}"
        )
