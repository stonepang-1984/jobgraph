"""Text embedding model."""


import numpy as np
from loguru import logger

from config.settings import settings


class TextEmbedder:
    """Text embedding using sentence-transformers or OpenAI."""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.embedding.text_model
        self.dimension = settings.embedding.text_dimension
        self._model = None

    @property
    def model(self):
        if self._model is None:
            self._load_model()
        return self._model

    def _load_model(self) -> None:
        """Load the embedding model."""
        logger.info(f"Loading embedding model: {self.model_name}")

        if self.model_name.startswith("text-embedding"):
            # OpenAI model - use API
            self._model = "openai"
        else:
            # Local model using sentence-transformers
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Model loaded: {self.model_name}")

    def embed(self, text: str) -> list[float]:
        """Embed a single text."""
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Embed a batch of texts."""
        if not texts:
            return []

        logger.debug(f"Embedding {len(texts)} texts")

        if self.model == "openai":
            return self._embed_openai(texts)
        else:
            return self._embed_local(texts, batch_size)

    def _embed_local(self, texts: list[str], batch_size: int) -> list[list[float]]:
        """Embed using local sentence-transformers model."""
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    def _embed_openai(self, texts: list[str]) -> list[list[float]]:
        """Embed using OpenAI API."""
        import openai

        client = openai.OpenAI(
            api_key=settings.llm.openai_api_key,
            base_url=settings.llm.openai_api_base,
        )

        response = client.embeddings.create(
            model=self.model_name,
            input=texts,
        )

        return [item.embedding for item in response.data]

    def similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))


# Singleton instance
text_embedder = TextEmbedder()
