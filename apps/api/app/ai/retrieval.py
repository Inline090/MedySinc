from uuid import UUID

import asyncpg

from app.ai.embeddings import get_embeddings
from app.repositories.chunks import search_chunks

DEFAULT_RESULTS = 6


async def find_relevant_chunks(
    *,
    user_id: UUID,
    query: str,
    limit: int = DEFAULT_RESULTS,
) -> list[asyncpg.Record]:
    embedding = (await get_embeddings().embed([query]))[0]

    return await search_chunks(user_id=user_id, embedding=embedding, limit=limit)
