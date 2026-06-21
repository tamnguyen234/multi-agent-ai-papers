import logging
from app.config import settings

logger = logging.getLogger(__name__)

class EmbeddingEngine:
    _instance = None
    _model = None
    _tried_loading = False
    _load_error = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_model(self):
        if self._tried_loading:
            if self._load_error:
                raise self._load_error
            return self._model

        self._tried_loading = True
        logger.info(f"Initializing SentenceTransformer model using {settings.TREND_EMBEDDING_MODEL}...")
        try:
            # Import lazy-loading to keep health-check fast and decouple dependencies
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(settings.TREND_EMBEDDING_MODEL)
            logger.info("SentenceTransformer model loaded successfully.")
            return self._model
        except Exception as e:
            self._load_error = RuntimeError(f"Embedding model load failed: {str(e)}")
            logger.error(f"Failed to load embedding model: {str(e)}", exc_info=True)
            raise self._load_error

    def is_loaded(self) -> bool:
        return self._model is not None
