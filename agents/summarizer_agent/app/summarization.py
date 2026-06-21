import re
import logging
from app.config import settings

logger = logging.getLogger(__name__)

def generate_extractive_summary(abstract: str) -> str:
    """
    Disabled paper summarization. Returns empty string.
    """
    return ""
