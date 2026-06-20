import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    QA_PORT = int(os.getenv("QA_PORT", "8103"))
    QA_HOST = os.getenv("QA_HOST", "127.0.0.1")
    
    QA_MODE = os.getenv("QA_MODE", "mock_fallback")
    QA_EMBEDDING_MODEL = os.getenv("QA_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    QA_LLM_PROVIDER = os.getenv("QA_LLM_PROVIDER", "ollama")
    QA_OLLAMA_BASE_URL = os.getenv("QA_OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
    QA_OLLAMA_MODEL = os.getenv("QA_OLLAMA_MODEL", os.getenv("OLLAMA_MODEL", "qwen2.5:3b"))
    QA_CHUNK_SIZE = int(os.getenv("QA_CHUNK_SIZE", "1000"))
    QA_CHUNK_OVERLAP = int(os.getenv("QA_CHUNK_OVERLAP", "150"))
    QA_TOP_K = int(os.getenv("QA_TOP_K", "5"))
    QA_INDEX_DIR = os.getenv("QA_INDEX_DIR", "../../data/faiss_indexes")
    QA_DATA_DIR = os.getenv("QA_DATA_DIR", "../../data")

settings = Settings()
