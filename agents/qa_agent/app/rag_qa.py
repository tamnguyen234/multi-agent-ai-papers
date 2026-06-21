import logging
from pathlib import Path
from app.path_resolver import resolve_pdf_path
from app.pdf_loader import load_pdf_pages
from app.chunking import chunk_pages
from app.vector_store import load_or_build_index, get_index_dir, verify_manifest, build_manifest
from app.llm_client import generate_llm_answer
from app.config import settings
from app.embeddings import EmbeddingEngine

logger = logging.getLogger(__name__)

# Global cache for reranker model
_reranker_model = None

def perform_rag_qa(paper_id: int, pdf_path: str, question: str, history: list[dict] | None = None) -> dict:
    """
    Executes advanced RAG pipeline: path resolution, PDF layout-aware loading,
    chunking, vector indexing (FAISS), candidate retrieval, CrossEncoder reranking
    using BAAI/bge-reranker-base, and LLM query generation.
    """
    # 1. Resolve path
    resolved_path = resolve_pdf_path(pdf_path)
    
    # 2. Try loading existing FAISS index first (skip PDF loading if index exists)
    index_dir = get_index_dir(paper_id)
    manifest = build_manifest(paper_id, resolved_path, settings.QA_CHUNK_SIZE, settings.QA_CHUNK_OVERLAP)
    db = None
    
    if index_dir.exists() and verify_manifest(index_dir, manifest):
        try:
            from langchain_community.vectorstores import FAISS
            embedding_model = EmbeddingEngine.get_instance().load_model()
            db = FAISS.load_local(str(index_dir), embedding_model, allow_dangerous_deserialization=True)
            logger.info(f"✅ Loaded cached FAISS index for paper {paper_id}")
        except Exception as e:
            logger.warning(f"Failed to load cached index, rebuilding: {e}")
            db = None
    
    # 3. If no cached index, do full PDF loading → chunking → indexing
    if db is None:
        pages_data = load_pdf_pages(str(resolved_path))
        chunks = chunk_pages(pages_data, paper_id)
        if not chunks:
            raise ValueError(f"No chunks extracted from PDF for paper {paper_id}")
        db, saved_chunks = load_or_build_index(paper_id, resolved_path, chunks)
    
    # 5. Retrieve candidates
    top_k = settings.QA_TOP_K
    initial_k = settings.QA_INITIAL_K
    
    logger.info(f"Retrieving top {initial_k} candidate chunks from FAISS...")
    docs_and_scores = db.similarity_search_with_score(question, k=initial_k)
    
    if not docs_and_scores:
        logger.warning("No candidate chunks found in FAISS.")
        return {
            "answer": "[Dự phòng] Không tìm thấy dữ liệu liên quan trong bài báo để trả lời.",
            "sources": []
        }
        
    # 6. CrossEncoder Reranking (BAAI/bge-reranker-base)
    global _reranker_model
    if _reranker_model is None:
        logger.info("Loading Cross-Encoder reranker model (BAAI/bge-reranker-base)...")
        from sentence_transformers import CrossEncoder
        _reranker_model = CrossEncoder("BAAI/bge-reranker-base")
        
    pairs = [[question, item[0].page_content] for item in docs_and_scores]
    logger.info(f"Computing reranker scores for {len(pairs)} candidate pairs...")
    rerank_scores = _reranker_model.predict(pairs)
    
    # Associate candidates with their reranker scores
    scored_candidates = []
    for idx, (doc, faiss_score) in enumerate(docs_and_scores):
        scored_candidates.append((doc, float(rerank_scores[idx])))
        
    # Sort by reranker score in descending order (highest score first)
    sorted_candidates = sorted(scored_candidates, key=lambda x: x[1], reverse=True)
    
    # Select the top_k best chunks
    selected_candidates = sorted_candidates[:top_k]
    logger.info(f"Reranked: selected top {len(selected_candidates)} chunks.")
    
    # Format sources for metadata return
    sources = []
    context_chunks = []
    
    for doc, score in selected_candidates:
        meta = doc.metadata
        page_num = meta.get("page", 1)
        chunk_id = meta.get("chunk_id", "unknown")
        
        # Limit excerpt to 500 characters
        text_excerpt = doc.page_content[:500]
        
        sources.append({
            "page": page_num,
            "chunk_id": chunk_id,
            "text": text_excerpt,
            "score": round(score, 4)  # Reranker CrossEncoder score
        })
        
        context_chunks.append({
            "page": page_num,
            "text": doc.page_content
        })
        
    # 7. Generate answer using LLM
    answer = generate_llm_answer(question, context_chunks, history=history)
    
    return {
        "answer": answer,
        "sources": sources
    }
