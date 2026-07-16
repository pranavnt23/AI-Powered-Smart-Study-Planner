import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating dense vector embeddings from text chunks.
    Adheres strictly to the Single Responsibility Principle, focusing solely
    on vector generation without database or storage logic.

    Uses the sentence-transformers library and the 'all-MiniLM-L6-v2' model
    producing 384-dimensional vectors.
    """

    _model = None

    @classmethod
    def _get_model(cls) -> SentenceTransformer:
        """
        Lazily loads the SentenceTransformer model to avoid blocking app startup
        times until an embedding generation is explicitly requested.
        """
        if cls._model is None:
            logger.info("Initializing SentenceTransformer 'all-MiniLM-L6-v2'...")
            # This downloads model weights locally on first use and loads into RAM/VRAM
            cls._model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("SentenceTransformer model loaded successfully.")
        return cls._model

    @classmethod
    def generate_embedding(cls, text: str) -> list[float]:
        """
        Generates a 384-dimensional dense vector embedding for a single text chunk.

        Args:
            text (str): Input text to encode.

        Returns:
            list[float]: A list containing 384 float dimensions.
        """
        if not text:
            return []

        try:
            model = cls._get_model()
            embedding = model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as error:
            logger.error(f"Failed to generate embedding: {str(error)}")
            raise error

    @classmethod
    def generate_embeddings_batch(cls, texts: list[str]) -> list[list[float]]:
        """
        Generates dense vector embeddings for multiple text chunks in a single batch.
        Batch processing maximizes performance through vector parallelization.

        Args:
            texts (list[str]): List of input text chunks to encode.

        Returns:
            list[list[float]]: List of 384-dimensional vector embeddings.
        """
        if not texts:
            return []

        try:
            model = cls._get_model()
            embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return embeddings.tolist()
        except Exception as error:
            logger.error(f"Failed to generate batch embeddings: {str(error)}")
            raise error
