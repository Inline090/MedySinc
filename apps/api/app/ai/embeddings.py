"""Turns text into search vectors."""

from functools import lru_cache
from typing import Protocol

import anyio
from sentence_transformers import SentenceTransformer

from app.core.config import settings


class EmbeddingProvider(Protocol):
    """The required structure for any embedding class."""

    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class SentenceTransformerEmbeddings:
    """Uses a local AI model (like bge-m3) to turn text into vectors."""

    def __init__(self, model_name: str) -> None:
        """Saves the model name to use later. Doesn't load it yet."""

        self._model_name = model_name
        self._model: SentenceTransformer | None = None

    def _load(self) -> SentenceTransformer:
        """Loads the model and checks if its output size matches the database."""

        if self._model is None:
            model = SentenceTransformer(self._model_name, cache_folder=settings.MODEL_CACHE_DIR)
            actual = model.get_embedding_dimension()

            if actual != settings.EMBEDDING_DIMENSION:
                raise RuntimeError(
                    f"Embedding model {self._model_name} produces {actual} dimensions "
                    f"but the schema expects {settings.EMBEDDING_DIMENSION}"
                )

            self._model = model

        return self._model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Turns a list of texts into search vectors."""

        if not texts:
            return []

        model = await anyio.to_thread.run_sync(self._load)

        return await anyio.to_thread.run_sync(self._encode, model, texts)

    @staticmethod
    def _encode(model: SentenceTransformer, texts: list[str]) -> list[list[float]]:
        """Runs the model and returns simple number lists."""

        return model.encode(texts, normalize_embeddings=True).tolist()


@lru_cache
def get_embeddings() -> EmbeddingProvider:
    """Gets the embedding tool, creating it if it doesn't exist yet."""

    return SentenceTransformerEmbeddings(settings.EMBEDDING_MODEL)
