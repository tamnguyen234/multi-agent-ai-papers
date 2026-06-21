import os
import logging
from app.config import settings
from app.schemas import QAAskRequest
from app.rag_qa import perform_rag_qa

logger = logging.getLogger(__name__)

def answer_question(payload: QAAskRequest) -> dict:
    logger.info(f"Q&A Request starting. Paper ID: {payload.paper_id}")
    
    # 1. Check Ollama and model existence
    import httpx
    ollama_url = f"{settings.QA_OLLAMA_BASE_URL.rstrip('/')}/api/tags"
    ollama_ok = False
    model_exists = False
    ollama_err_msg = ""
    
    try:
        resp = httpx.get(ollama_url, timeout=3.0)
        if resp.status_code == 200:
            ollama_ok = True
            data = resp.json()
            models = [m.get("name") for m in data.get("models", [])]
            model_exists = settings.QA_OLLAMA_MODEL in models or any(settings.QA_OLLAMA_MODEL in m for m in models)
            if not model_exists:
                ollama_err_msg = f"Model '{settings.QA_OLLAMA_MODEL}' not found in Ollama. Available: {models}"
        else:
            ollama_err_msg = f"Ollama server returned status code {resp.status_code}"
    except Exception as e:
        ollama_err_msg = f"Ollama connection error: {str(e)}"
        
    if not ollama_ok or not model_exists:
        # Ollama check failed, trigger fallback
        logger.warning(f"Ollama check failed: {ollama_err_msg}. Triggering fallback.")
        
        # Fallback level 1: Extract PDF text chunks directly (without LLM)
        try:
            from app.path_resolver import resolve_pdf_path
            from app.pdf_loader import load_pdf_pages
            from app.chunking import chunk_pages
            from app.vector_store import load_or_build_index
            
            resolved_path = resolve_pdf_path(payload.pdf_path)
            pages_data = load_pdf_pages(str(resolved_path))
            chunks = chunk_pages(pages_data, payload.paper_id)
            db, saved_chunks = load_or_build_index(payload.paper_id, resolved_path, chunks)
            
            docs_and_scores = db.similarity_search_with_score(payload.question, k=3)
            formatted_sources = []
            for doc, score in docs_and_scores:
                meta = doc.metadata
                formatted_sources.append({
                    "page": meta.get("page", 1),
                    "chunk_id": meta.get("chunk_id", "unknown"),
                    "text": doc.page_content[:500],
                    "score": round(float(score), 4)
                })
            
            chunks_text = " | ".join([f"[Trang {doc.metadata.get('page')}]: {doc.page_content[:200]}..." for doc, _ in docs_and_scores])
            answer = f"[Dự phòng - Ollama offline] Không thể kết nối với mô hình Ollama. Trích xuất trực tiếp từ bài viết: {chunks_text}"
            return {
                "answer": answer,
                "sources": formatted_sources,
                "mode": "fallback_ollama_offline",
                "fallback_reason": f"Ollama check failed: {ollama_err_msg}",
                "error": ollama_err_msg
            }
        except Exception as inner_e:
            logger.error(f"PDF fallback failed: {str(inner_e)}")
            
        # Fallback level 2: Use abstract/summary if PDF chunks extraction failed
        if payload.summary or payload.abstract:
            context = payload.summary or payload.abstract or ""
            answer = f"[Dự phòng - Chỉ dựa trên Abstract/Summary] Không thể phân tích nội dung PDF hoặc kết nối với Ollama. Nội dung chính: {context[:300]}..."
            return {
                "answer": answer,
                "sources": [],
                "mode": "fallback_ollama_offline",
                "fallback_reason": f"RAG and PDF parse failed: {ollama_err_msg}",
                "error": ollama_err_msg
            }
            
        # Return baseline offline structure
        return {
            "answer": f"[Dự phòng - Ollama offline] Không thể kết nối với mô hình Ollama: {ollama_err_msg}",
            "sources": [],
            "mode": "fallback_ollama_offline",
            "fallback_reason": f"Ollama offline: {ollama_err_msg}",
            "error": ollama_err_msg
        }

    # 2. Ollama check succeeded, run real RAG QA
    try:
        res = perform_rag_qa(payload.paper_id, payload.pdf_path, payload.question, history=payload.history)
        return {
            "answer": res["answer"],
            "sources": res["sources"],
            "mode": "real",
            "fallback_reason": None,
            "error": None
        }
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"Real QA failed during execution, trying fallback. Reason: {error_msg}")
        
        # Fallback level 1: Extract PDF text chunks directly
        try:
            from app.path_resolver import resolve_pdf_path
            from app.pdf_loader import load_pdf_pages
            from app.chunking import chunk_pages
            from app.vector_store import load_or_build_index
            
            resolved_path = resolve_pdf_path(payload.pdf_path)
            pages_data = load_pdf_pages(str(resolved_path))
            chunks = chunk_pages(pages_data, payload.paper_id)
            db, saved_chunks = load_or_build_index(payload.paper_id, resolved_path, chunks)
            
            docs_and_scores = db.similarity_search_with_score(payload.question, k=3)
            formatted_sources = []
            for doc, score in docs_and_scores:
                meta = doc.metadata
                formatted_sources.append({
                    "page": meta.get("page", 1),
                    "chunk_id": meta.get("chunk_id", "unknown"),
                    "text": doc.page_content[:500],
                    "score": round(float(score), 4)
                })
            
            chunks_text = " | ".join([f"[Trang {doc.metadata.get('page')}]: {doc.page_content[:200]}..." for doc, _ in docs_and_scores])
            answer = f"[Dự phòng - Ollama offline] Không thể kết nối với mô hình Ollama. Trích xuất trực tiếp từ bài viết: {chunks_text}"
            return {
                "answer": answer,
                "sources": formatted_sources,
                "mode": "fallback_ollama_offline",
                "fallback_reason": f"Real QA execution failed: {error_msg}",
                "error": error_msg
            }
        except Exception as inner_e:
            logger.error(f"PDF fallback failed: {str(inner_e)}")
            
        # Fallback level 2: Use abstract/summary
        if payload.summary or payload.abstract:
            context = payload.summary or payload.abstract or ""
            answer = f"[Dự phòng - Chỉ dựa trên Abstract/Summary] Không thể phân tích nội dung PDF hoặc kết nối với Ollama. Nội dung chính: {context[:300]}..."
            return {
                "answer": answer,
                "sources": [],
                "mode": "fallback_ollama_offline",
                "fallback_reason": f"RAG and PDF parse failed: {error_msg}",
                "error": error_msg
            }
            
        return {
            "answer": f"[Dự phòng - Ollama offline] Lỗi gọi mô hình Ollama: {error_msg}",
            "sources": [],
            "mode": "fallback_ollama_offline",
            "fallback_reason": f"Execution failed: {error_msg}",
            "error": error_msg
        }
