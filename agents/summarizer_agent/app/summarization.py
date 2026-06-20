import re
import logging
from app.config import settings

logger = logging.getLogger(__name__)

def generate_extractive_summary(abstract: str) -> str:
    """
    Generate a simple extractive summary from the abstract by taking the first 2-3 sentences.
    Capped at SUMMARY_MAX_CHARS and SUMMARY_MAX_SENTENCES to ensure it is brief and fits database columns.
    Only uses text from the abstract without generating external hallucinations.
    """
    if not abstract or not abstract.strip():
        return ""
        
    text = abstract.strip()
    
    # Lightweight sentence splitter using regex
    # Ignores abbreviations like 'e.g.', 'i.e.', 'et al.', and single initials followed by a dot
    sentence_endings = re.compile(
        r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<!et al\.)(?<!e\.g\.)(?<!i\.e\.)(?<=\.|\?)\s'
    )
    sentences = sentence_endings.split(text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        # Fallback to simple slice if splitting failed
        return text[:settings.SUMMARY_MAX_CHARS].strip()
        
    summary_sentences = []
    current_length = 0
    
    for s in sentences:
        if len(summary_sentences) >= settings.SUMMARY_MAX_SENTENCES:
            break
            
        potential_len = current_length + len(s) + (1 if summary_sentences else 0)
        if potential_len <= settings.SUMMARY_MAX_CHARS:
            summary_sentences.append(s)
            current_length = potential_len
        else:
            # If first sentence exceeds the limit, add it truncated
            if not summary_sentences:
                truncated = s[:settings.SUMMARY_MAX_CHARS - 4].strip() + "..."
                summary_sentences.append(truncated)
            break
            
    summary_text = " ".join(summary_sentences)
    return summary_text
