import logging
from typing import List, Dict
import fitz
import pymupdf4llm

logger = logging.getLogger(__name__)

def load_pdf_pages(pdf_path: str) -> List[Dict]:
    """
    Extracts markdown text and page numbers from a PDF file using pymupdf4llm.
    """
    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    doc.close()

    pages = []
    for page_idx in range(num_pages):
        page_num = page_idx + 1
        page_text = pymupdf4llm.to_markdown(pdf_path, pages=[page_idx])
        pages.append({
            "page": page_num,
            "text": page_text
        })

    return pages
