from dataclasses import dataclass
from typing import NotRequired, TypedDict, cast
from uuid import UUID

from app.ai.embeddings import get_embeddings
from app.ai.reranker import get_reranker
from app.core.config import settings
from app.repositories.chunks import search_chunks_by_text, search_chunks_by_vector

RECALL_SIZE = 20
DEFAULT_RESULTS = 6
RRF_K = 60


class RetrievedChunk(TypedDict):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    token_count: int
    document_title: str
    document_type: str
    similarity: float
    score: float
    rerank_score: NotRequired[float]


@dataclass(frozen=True)
class Retrieval:
    chunks: list[RetrievedChunk]
    best_similarity: float


def reciprocal_rank_fusion(rankings: list[list[UUID]], k: int = RRF_K) -> list[tuple[UUID, float]]:
    scores: dict[UUID, float] = {}

    for ranking in rankings:
        for position, key in enumerate(ranking, start=1):
            scores[key] = scores.get(key, 0.0) + 1 / (k + position)

    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


async def _rerank(query: str, pool: list[RetrievedChunk]) -> list[RetrievedChunk]:
    scores = await get_reranker().rerank(query, [chunk["content"] for chunk in pool])

    for chunk, score in zip(pool, scores, strict=True):
        chunk["rerank_score"] = score

    return sorted(pool, key=lambda chunk: chunk.get("rerank_score", 0.0), reverse=True)


async def find_relevant_chunks(
    *,
    user_id: UUID,
    query: str,
    limit: int = DEFAULT_RESULTS,
    recall: int = RECALL_SIZE,
) -> Retrieval:
    embedding = (await get_embeddings().embed([query]))[0]

    vector_rows = await search_chunks_by_vector(
        user_id=user_id,
        embedding=embedding,
        limit=recall,
    )
    text_rows = await search_chunks_by_text(
        user_id=user_id,
        embedding=embedding,
        query=query,
        limit=recall,
    )

    candidates = {row["id"]: dict(row) for row in [*vector_rows, *text_rows]}

    fused = reciprocal_rank_fusion(
        [
            [row["id"] for row in vector_rows],
            [row["id"] for row in text_rows],
        ]
    )

    pool: list[RetrievedChunk] = []

    for chunk_id, score in fused[: settings.RERANK_CANDIDATES]:
        candidate = candidates[chunk_id]
        candidate["score"] = score
        pool.append(cast(RetrievedChunk, candidate))

    best_similarity = max((chunk["similarity"] for chunk in pool), default=0.0)

    if not settings.RERANK_ENABLED or not pool:
        return Retrieval(chunks=pool[:limit], best_similarity=best_similarity)

    return Retrieval(chunks=(await _rerank(query, pool))[:limit], best_similarity=best_similarity)
