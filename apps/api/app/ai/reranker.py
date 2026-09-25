from functools import lru_cache
from typing import Protocol

import anyio
from sentence_transformers import CrossEncoder

from app.core.config import settings


class Reranker(Protocol):
    async def rerank(self, query: str, documents: list[str]) -> list[float]: ...


class CrossEncoderReranker:
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model: CrossEncoder | None = None

    def _load(self) -> CrossEncoder:
        if self._model is None:
            self._model = CrossEncoder(
                self._model_name,
                cache_folder=settings.MODEL_CACHE_DIR,
            )

        return self._model

    async def rerank(self, query: str, documents: list[str]) -> list[float]:
        if not documents:
            return []

        model = await anyio.to_thread.run_sync(self._load)

        return await anyio.to_thread.run_sync(self._score, model, query, documents)

    @staticmethod
    def _score(model: CrossEncoder, query: str, documents: list[str]) -> list[float]:
        pairs = [(query, document) for document in documents]

        return [float(score) for score in model.predict(pairs)]


@lru_cache
def get_reranker() -> Reranker:
    return CrossEncoderReranker(settings.RERANKER_MODEL)
