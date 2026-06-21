import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SUMMARIZER_PORT = int(os.getenv("SUMMARIZER_PORT", "8101"))
    SUMMARIZER_HOST = os.getenv("SUMMARIZER_HOST", "127.0.0.1")
    SUMMARIZER_MODE = os.getenv("SUMMARIZER_MODE", "mock_fallback").lower().strip()
    
    ARXIV_CATEGORIES = os.getenv("ARXIV_CATEGORIES", "cs.AI,cs.CL,cs.LG,cs.CV,cs.RO,cs.SD").split(",")
    ARXIV_MAX_RESULTS = int(os.getenv("ARXIV_MAX_RESULTS", "50"))
    ARXIV_DAYS_BACK = int(os.getenv("ARXIV_DAYS_BACK", "2"))
    
    SUMMARY_MAX_SENTENCES = int(os.getenv("SUMMARY_MAX_SENTENCES", "3"))
    SUMMARY_MAX_CHARS = int(os.getenv("SUMMARY_MAX_CHARS", "700"))

settings = Settings()
