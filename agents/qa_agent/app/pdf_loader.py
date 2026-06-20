import logging
from typing import List, Dict
import fitz
import pymupdf4llm

logger = logging.getLogger(__name__)

def load_pdf_pages(pdf_path: str) -> List[Dict]:
    """
    Extracts markdown text and page numbers from a PDF file using pymupdf4llm.
    Falls back to standard PyMuPDF if pymupdf4llm fails.
    """
    try:
        doc = fitz.open(pdf_path)
        num_pages = len(doc)
        doc.close()
    except Exception as e:
        logger.error(f"Failed to open PDF file {pdf_path}: {e}")
        raise
        
    pages = []
    for page_idx in range(num_pages):
        page_num = page_idx + 1
        try:
            # Extract page as markdown
            page_text = pymupdf4llm.to_markdown(pdf_path, pages=[page_idx])
            if not page_text or not page_text.strip():
                # Fallback to standard PyMuPDF if empty
                raise ValueError("Empty markdown content")
        except Exception as exc:
            logger.debug(f"pymupdf4llm page {page_num} extraction failed: {exc}, falling back to standard PyMuPDF")
            try:
                doc = fitz.open(pdf_path)
                page = doc[page_idx]
                page_text = page.get_text()
                doc.close()
            except Exception as inner_exc:
                logger.error(f"Fallback text extraction failed for page {page_num}: {inner_exc}")
                page_text = ""
                
        pages.append({
            "page": page_num,
            "text": page_text
        })
        
    return pages
