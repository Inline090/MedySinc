from uuid import UUID

from app.ai.embeddings import get_embeddings
from app.repositories.chunks import search_chunks_by_text, search_chunks_by_vector

RECALL_SIZE = 20
DEFAULT_RESULTS = 6
RRF_K = 60


def reciprocal_rank_fusion(rankings: list[list[UUID]], k: int = RRF_K) -> list[tuple[UUID, float]]:
    scores: dict[UUID, float] = {}

    for ranking in rankings:
        for position, key in enumerate(ranking, start=1):
            scores[key] = scores.get(key, 0.0) + 1 / (k + position)

    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


async def find_relevant_chunks(
    *,
    user_id: UUID,
    query: str,
    limit: int = DEFAULT_RESULTS,
    recall: int = RECALL_SIZE,
) -> list[dict[str, object]]:
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

    results: list[dict[str, object]] = []

    for chunk_id, score in fused[:limit]:
        candidate = candidates[chunk_id]
        candidate["score"] = score
        results.append(candidate)

    return results
