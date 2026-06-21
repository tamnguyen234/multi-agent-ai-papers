import os
import re
import httpx
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.db.models.paper import Paper
from app.services import storage_service
from app.core.config import settings

logger = logging.getLogger(__name__)

def extract_external_id(external_id: str) -> str:
    """
    Extract and normalize the external_id from various formats.
    Examples:
      - "2401.12345" -> "2401.12345"
      - "2401.12345v2" -> "2401.12345v2"
      - "arXiv:2401.12345v2" -> "2401.12345v2"
      - "https://arxiv.org/abs/2401.12345" -> "2401.12345"
      - "https://arxiv.org/pdf/2401.12345.pdf" -> "2401.12345"
      - "cs/9901001" -> "cs/9901001"
    """
    val = external_id.strip()
    
    # Check if it is a full URL
    if val.startswith("http://") or val.startswith("https://"):
        # Match pattern /(pdf|abs)/<id>(.pdf)?
        match = re.search(r'/(?:pdf|abs)/([a-zA-Z0-9\-./]+?)(?:\.pdf)?$', val)
        if match:
            return match.group(1)
            
    if val.lower().startswith("arxiv:"):
        val = val[len("arxiv:"):].strip()
        
    return val

def build_arxiv_pdf_url(external_id: str) -> str:
    """
    If external_id looks like a full URL already, return it directly.
    Otherwise extract the normalized external_id and build the arxiv PDF link.
    """
    val = external_id.strip()
    if val.startswith("http://") or val.startswith("https://"):
        if val.lower().endswith(".pdf"):
            return val
        extracted = extract_external_id(val)
        return f"https://arxiv.org/pdf/{extracted}.pdf"
        
    extracted = extract_external_id(val)
    return f"https://arxiv.org/pdf/{extracted}.pdf"

def download_pdf_bytes(pdf_url: str) -> bytes:
    """
    Download PDF bytes from pdf_url with timeout and safety checks.
    """
    timeout = settings.PDF_DOWNLOAD_TIMEOUT_SECONDS
    max_size_bytes = settings.MAX_PDF_SIZE_MB * 1024 * 1024
    
    try:
        # Create httpx client with follow_redirects=True
        with httpx.Client(follow_redirects=True, timeout=float(timeout)) as client:
            response = client.get(pdf_url)
            
            # Only accept HTTP 200
            if response.status_code != 200:
                raise ValueError(f"Failed to download PDF. HTTP status code: {response.status_code}")
                
            # Validate size from headers if available
            content_length = response.headers.get("Content-Length")
            if content_length:
                try:
                    size = int(content_length)
                    if size > max_size_bytes:
                        raise ValueError(f"PDF file size ({size} bytes) exceeds limit of {settings.MAX_PDF_SIZE_MB} MB")
                except ValueError as ve:
                    if "exceeds limit" in str(ve):
                        raise ve
                    pass
            
            file_bytes = response.content
            
            # Validate size of downloaded bytes
            if len(file_bytes) > max_size_bytes:
                raise ValueError(f"PDF file size ({len(file_bytes)} bytes) exceeds limit of {settings.MAX_PDF_SIZE_MB} MB")
                
            # Validate content-type or magic header starts with %PDF
            content_type = response.headers.get("Content-Type", "").lower()
            
            # Starts with b"%PDF" (validate first 4 bytes)
            if not file_bytes.startswith(b"%PDF"):
                raise ValueError("Downloaded file does not start with %PDF magic header")
                
            return file_bytes
            
    except httpx.HTTPError as he:
        raise ValueError(f"HTTP connection error: {str(he)}")
    except Exception as e:
        raise ValueError(f"Error downloading PDF: {str(e)}")

def download_and_attach_pdf(db: Session, paper_id: int) -> dict:
    """
    Finds paper, downloads its PDF, saves it, updates db with relative path.
    """
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper with ID {paper_id} not found."
        )
        
    # Check if paper already has pdf_path and if file exists on disk
    project_root = storage_service.get_project_root()
    if paper.pdf_path:
        full_path = project_root / paper.pdf_path.lstrip("/")
        if os.path.exists(full_path):
            size_bytes = os.path.getsize(full_path)
            return {
                "paper_id": paper.id,
                "mode": "existing",
                "pdf_path": paper.pdf_path,
                "pdf_url": paper.pdf_url,
                "source_pdf_url": build_arxiv_pdf_url(paper.external_id) if paper.external_id else None,
                "size_bytes": size_bytes
            }
            
    if not paper.external_id or not paper.external_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paper does not have a valid external_id for PDF download."
        )
        
    source_pdf_url = build_arxiv_pdf_url(paper.external_id)
    
    logger.info(f"Downloading PDF from {source_pdf_url} for paper ID {paper.id}")
    try:
        pdf_bytes = download_pdf_bytes(source_pdf_url)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download PDF: {str(e)}"
        )
        
    # Save the file using storage service
    try:
        filename = f"{extract_external_id(paper.external_id)}.pdf"
        saved_file_info = storage_service.save_paper_pdf_bytes(pdf_bytes, original_filename=filename)
    except Exception as se:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save PDF file to disk: {str(se)}"
        )
        
    # Update DB
    relative_path = saved_file_info["relative_path"]
    try:
        paper.pdf_path = relative_path
        db.commit()
        db.refresh(paper)
    except Exception as dbe:
        db.rollback()
        # Clean up file on failure
        full_path_to_delete = project_root / relative_path.lstrip("/")
        if os.path.exists(full_path_to_delete):
            try:
                os.remove(full_path_to_delete)
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database update failed. Rolled back file save: {str(dbe)}"
        )
        
    return {
        "paper_id": paper.id,
        "mode": "downloaded",
        "pdf_path": paper.pdf_path,
        "pdf_url": paper.pdf_url,
        "source_pdf_url": source_pdf_url,
        "size_bytes": saved_file_info["size_bytes"]
    }
