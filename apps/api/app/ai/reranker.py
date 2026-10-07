"""Re-scores the best search results by looking at them more closely."""

from functools import lru_cache
from typing import Protocol

import anyio
from sentence_transformers import CrossEncoder

from app.core.config import settings


class Reranker(Protocol):
    """The required structure for any reranker class."""

    async def rerank(self, query: str, documents: list[str]) -> list[float]: ...


class CrossEncoderReranker:
    """Uses an AI model (like MiniLM) to score how well a document answers a question."""

    def __init__(self, model_name: str) -> None:
        """Saves the model name to use later. Doesn't load it yet."""

        self._model_name = model_name
        self._model: CrossEncoder | None = None

    def _load(self) -> CrossEncoder:
        """Loads the model and saves it so we can reuse it."""

        if self._model is None:
            self._model = CrossEncoder(
                self._model_name,
                cache_folder=settings.MODEL_CACHE_DIR,
            )

        return self._model

    async def rerank(self, query: str, documents: list[str]) -> list[float]:
        """Scores a list of documents based on how well they answer the question."""

        if not documents:
            return []

        model = await anyio.to_thread.run_sync(self._load)

        return await anyio.to_thread.run_sync(self._score, model, query, documents)

    @staticmethod
    def _score(model: CrossEncoder, query: str, documents: list[str]) -> list[float]:
        """Runs the model on pairs of (question, document)."""

        pairs = [(query, document) for document in documents]

        return [float(score) for score in model.predict(pairs)]


@lru_cache
def get_reranker() -> Reranker:
    """Gets the reranking tool, creating it if it doesn't exist yet."""

    return CrossEncoderReranker(settings.RERANKER_MODEL)
