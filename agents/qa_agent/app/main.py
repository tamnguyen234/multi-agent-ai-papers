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

class IndexRequest(BaseModel):
    paper_id: int
    pdf_path: str

class QueryRequest(BaseModel):
    paper_id: int
    question: str

@app.get("/health")
def health_check():
    """Return health check status."""
    from app.embeddings import EmbeddingEngine
    from app.config import settings
    import httpx

    url = f"{settings.QA_OLLAMA_BASE_URL.rstrip('/')}/api/tags"
    response = httpx.get(url, timeout=1.5)
    ollama_reachable = response.status_code == 200
    data = response.json() if ollama_reachable else {}
    ollama_models = [m.get("name") for m in data.get("models", [])]

    return {
        "status": "ok",
        "service": "qa_agent",
        "embedding_model_loaded": EmbeddingEngine.get_instance().is_loaded(),
        "llm_provider": settings.QA_LLM_PROVIDER,
        "ollama_base_url": settings.QA_OLLAMA_BASE_URL,
        "ollama_model": settings.QA_OLLAMA_MODEL,
        "ollama_reachable": ollama_reachable,
        "ollama_models": ollama_models,
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

    res = answer_question(payload)
    return QAAskResponse(**res)
