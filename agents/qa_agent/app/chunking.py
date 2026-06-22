import re
import logging
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings

logger = logging.getLogger(__name__)

EXCLUDE_KEYWORDS = [
    "reference", "bibliography", "bibliograph",
    "acknowledgment", "acknowledgement",
    "appendix", "supplementary", "supplement",
    "ablation",
]

def _normalize_headings(md_text: str) -> str:
    """Convert bold-only lines to ## headings (strict rules)."""
    def _is_heading(match: re.Match) -> str:
        text = match.group(1).strip()
        if len(text) > 60:
            return match.group(0)
        if text.endswith('.') or '. ' in text:
            return match.group(0)
        if any(c in text for c in ('@', '{', ',', '**')):
            return match.group(0)
        if text[0].islower():
            return match.group(0)
        return f'## {text}'

    return re.sub(
        r'^\s*\*\*(.{3,100}?)\*\*\s*$',
        _is_heading, md_text, flags=re.MULTILINE,
    )

def _protect_tables(md_text: str) -> str:
    """Join table rows so the splitter won't cut mid-table."""
    MARKER = "\x00"
    lines = md_text.split("\n")
    result = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        is_table = stripped.startswith("|") or stripped.startswith("|-")
        if is_table:
            if in_table:
                result.append(MARKER + line)
            else:
                in_table = True
                result.append(line)
        else:
            in_table = False
            result.append(line)
    return "\n".join(result)

def chunk_pages(pages_data: List[Dict], paper_id: int) -> List[Dict]:
    """
    Split page texts into chunks using advanced markdown-aware splitter,
    protecting tables, normalising headings, and filtering out noise sections.
    """
    chunk_size = settings.QA_CHUNK_SIZE
    chunk_overlap = settings.QA_CHUNK_OVERLAP
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n### ", "\n#### ", "\n\n", "\n", ". ", " "],
        length_function=len
    )
    
    chunks = []
    chunk_idx = 0
    last_heading = ""
    
    for page in pages_data:
        page_num = page["page"]
        raw_text = page["text"]
        if not raw_text or not raw_text.strip():
            continue
            
        # 1. Normalize headings & Protect tables
        normalized_text = _normalize_headings(raw_text)
        protected_text = _protect_tables(normalized_text)
        
        # 2. Split page text
        page_chunks = splitter.split_text(protected_text)
        
        for pc in page_chunks:
            # Restore tables in the chunk
            restored_text = pc.replace("\x00", "\n").strip()

            # Agent2 behavior: keep the latest section heading on continuation chunks.
            heading_match = re.match(r'^(#{1,6}\s+.+)', restored_text)
            if heading_match and '**' not in heading_match.group(1):
                last_heading = heading_match.group(1)
            elif last_heading:
                restored_text = last_heading + "\n\n" + restored_text
            
            if len(restored_text) < 50:
                continue
                
            # Filter noise keywords in the chunk
            lower_excerpt = restored_text[:300].lower()
            if any(kw in lower_excerpt for kw in EXCLUDE_KEYWORDS):
                continue
                
            chunks.append({
                "chunk_id": f"paper_{paper_id}_chunk_{chunk_idx}",
                "paper_id": paper_id,
                "page": page_num,
                "chunk_index": chunk_idx,
                "text": restored_text
            })
            chunk_idx += 1
            
    logger.info(f"Chunking: split {len(pages_data)} pages into {len(chunks)} filtered chunks.")
    return chunks
