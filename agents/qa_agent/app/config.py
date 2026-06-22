import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    QA_PORT = int(os.getenv("QA_PORT", "8103"))
    QA_HOST = os.getenv("QA_HOST", "127.0.0.1")
    
    QA_EMBEDDING_MODEL = os.getenv("QA_EMBEDDING_MODEL", "nomic-embed-text")
    QA_LLM_PROVIDER = os.getenv("QA_LLM_PROVIDER", "ollama")
    QA_OLLAMA_BASE_URL = os.getenv("QA_OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    QA_OLLAMA_MODEL = os.getenv("QA_OLLAMA_MODEL", os.getenv("OLLAMA_MODEL", "qwen3.5:4b"))
    QA_CHUNK_SIZE = int(os.getenv("QA_CHUNK_SIZE", "5000"))
    QA_CHUNK_OVERLAP = int(os.getenv("QA_CHUNK_OVERLAP", "800"))
    QA_TOP_K = int(os.getenv("QA_TOP_K", "3"))
    QA_INITIAL_K = int(os.getenv("QA_INITIAL_K", "6"))
    QA_CONTEXT_MAX_CHARS = int(os.getenv("QA_CONTEXT_MAX_CHARS", "5000"))
    QA_OLLAMA_NUM_CTX = int(os.getenv("QA_OLLAMA_NUM_CTX", "8192"))
    QA_OLLAMA_NUM_PREDICT = int(os.getenv("QA_OLLAMA_NUM_PREDICT", "4096"))
    QA_OLLAMA_TEMPERATURE = float(os.getenv("QA_OLLAMA_TEMPERATURE", "0.1"))
    QA_OLLAMA_TIMEOUT_SECONDS = float(os.getenv("QA_OLLAMA_TIMEOUT_SECONDS", "600"))
    QA_INDEX_DIR = os.getenv("QA_INDEX_DIR", "../../data/indices_v2")
    QA_DATA_DIR = os.getenv("QA_DATA_DIR", "../../data")

settings = Settings()
