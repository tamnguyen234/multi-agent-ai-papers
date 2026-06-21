import os
import json
from pathlib import Path
from typing import List, Dict, Tuple, Any
from app.config import settings
from app.embeddings import EmbeddingEngine

def get_index_dir(paper_id: int) -> Path:
    base_dir = Path(settings.QA_INDEX_DIR).resolve()
    return base_dir / f"paper_{paper_id}"

def build_manifest(paper_id: int, pdf_path: Path, chunk_size: int, chunk_overlap: int) -> dict:
    stat = pdf_path.stat()
    return {
        "paper_id": paper_id,
        "pdf_path": str(pdf_path.as_posix()),
        "file_size": stat.st_size,
        "modified_time": stat.st_mtime,
        "embedding_model": settings.QA_EMBEDDING_MODEL,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap
    }

def verify_manifest(index_dir: Path, manifest: dict) -> bool:
    manifest_path = index_dir / "manifest.json"
    if not manifest_path.exists():
        return False
    with open(manifest_path, "r", encoding="utf-8") as f:
        existing = json.load(f)
    for key in ["pdf_path", "file_size", "modified_time", "embedding_model", "chunk_size", "chunk_overlap"]:
        if existing.get(key) != manifest.get(key):
            return False
    return True

def load_or_build_index(paper_id: int, pdf_path: Path, chunks: List[Dict]) -> Tuple[Any, List[Dict]]:
    """
    Load index from disk if it exists and is up to date, otherwise build and save it.
    Returns (faiss_index, chunks_metadata).
    """
    from langchain_community.vectorstores import FAISS
    
    index_dir = get_index_dir(paper_id)
    manifest = build_manifest(paper_id, pdf_path, settings.QA_CHUNK_SIZE, settings.QA_CHUNK_OVERLAP)
    
    embedding_model = EmbeddingEngine.get_instance().load_model()
    
    # Check if index exists and manifest is valid
    if index_dir.exists() and verify_manifest(index_dir, manifest):
        db = FAISS.load_local(str(index_dir), embedding_model, allow_dangerous_deserialization=True)
        with open(index_dir / "metadata.json", "r", encoding="utf-8") as f:
            saved_chunks = json.load(f)
        return db, saved_chunks
            
    # Build new index
    from langchain_core.documents import Document
    
    documents = [
        Document(
            page_content=c["text"],
            metadata={
                "chunk_id": c["chunk_id"],
                "paper_id": c["paper_id"],
                "page": c["page"],
                "chunk_index": c["chunk_index"]
            }
        )
        for c in chunks
    ]
    
    db = FAISS.from_documents(documents, embedding_model)
    
    # Save index to disk
    os.makedirs(index_dir, exist_ok=True)
    db.save_local(str(index_dir))
    
    # Save metadata
    with open(index_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
        
    # Save manifest
    with open(index_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    return db, chunks
