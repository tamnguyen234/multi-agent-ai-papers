import logging
from app.config import settings
from app.schemas import QAAskRequest
from app.rag_qa import perform_rag_qa

logger = logging.getLogger(__name__)

def answer_question(payload: QAAskRequest) -> dict:
    logger.info(f"Q&A Request starting. Paper ID: {payload.paper_id}")

    res = perform_rag_qa(payload.paper_id, payload.pdf_path, payload.question, history=payload.history)
    return {
        "answer": res["answer"],
        "sources": res["sources"],
        "mode": "real",
        "fallback_reason": None,
        "error": None,
    }
