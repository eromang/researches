"""Embedding model wrapper for ChromaDB."""

from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """Lazy-loaded sentence transformer for vulnerability descriptions."""

    DEFAULT_MODEL = "all-MiniLM-L6-v2"

    def __init__(self, model_name: str | None = None):
        self._model_name = model_name or self.DEFAULT_MODEL
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Encode texts to embeddings."""
        return self.model.encode(texts, show_progress_bar=False).tolist()
