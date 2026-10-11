from typing import Any

from app.base.config import ModelConfig


class SentenceTransformerEmbeddingModel:
    """Lazy adapter around the project's SentenceTransformer embedding model."""

    def __init__(
        self,
        model_name: str = ModelConfig.EMBEDDING_MODEL_NAME,
        model: Any | None = None,
    ):
        self.model_name = model_name
        self._model = model

    def _get_model(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, text: str) -> list[float]:
        encoded = self._get_model().encode(text)
        if hasattr(encoded, "tolist"):
            encoded = encoded.tolist()
        return list(encoded)
