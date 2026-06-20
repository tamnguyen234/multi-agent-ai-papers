import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    TREND_PORT = int(os.getenv("TREND_PORT", "8102"))
    TREND_HOST = os.getenv("TREND_HOST", "127.0.0.1")
    TREND_MODE = os.getenv("TREND_MODE", "rule_based_fallback")
    TREND_EMBEDDING_MODEL = os.getenv("TREND_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    TREND_MIN_TOPIC_SIZE = int(os.getenv("TREND_MIN_TOPIC_SIZE", "2"))
    TREND_TOP_N_WORDS = int(os.getenv("TREND_TOP_N_WORDS", "8"))
    TREND_UMAP_N_NEIGHBORS = int(os.getenv("TREND_UMAP_N_NEIGHBORS", "5"))
    TREND_UMAP_N_COMPONENTS = int(os.getenv("TREND_UMAP_N_COMPONENTS", "5"))
    TREND_HDBSCAN_MIN_CLUSTER_SIZE = int(os.getenv("TREND_HDBSCAN_MIN_CLUSTER_SIZE", "2"))

settings = Settings()
