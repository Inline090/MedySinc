from uuid import UUID

import asyncpg

from app.core.config import settings
from app.db.session import get_pool


def _to_vector(embedding: list[float]) -> str:
    return "[" + ",".join(str(value) for value in embedding) + "]"


async def replace_document_chunks(
    *,
    document_id: UUID,
    user_id: UUID,
    chunks: list[tuple[int, str, int, list[float]]],
) -> None:
    pool = get_pool()

    async with pool.acquire() as connection, connection.transaction():
        await connection.execute(
            "DELETE FROM document_chunks WHERE document_id = $1",
            document_id,
        )

        await connection.executemany(
            """
                INSERT INTO document_chunks (
                    document_id, user_id, chunk_index, content, token_count, embedding
                )
                VALUES ($1, $2, $3, $4, $5, $6::vector)
                """,
            [
                (document_id, user_id, index, content, token_count, _to_vector(embedding))
                for index, content, token_count, embedding in chunks
            ],
        )


async def count_document_chunks(document_id: UUID) -> int:
    pool = get_pool()

    return await pool.fetchval(
        "SELECT count(*) FROM document_chunks WHERE document_id = $1",
        document_id,
    )


async def find_chunks_for_document(document_id: UUID) -> list[asyncpg.Record]:
    pool = get_pool()

    return await pool.fetch(
        """
        SELECT chunk_index, content, token_count
        FROM document_chunks
        WHERE document_id = $1
        ORDER BY chunk_index
        """,
        document_id,
    )


async def search_chunks(
    *,
    user_id: UUID,
    embedding: list[float],
    limit: int,
) -> list[asyncpg.Record]:
    pool = get_pool()
    vector = _to_vector(embedding)

    async with pool.acquire() as connection, connection.transaction():
        await connection.execute(f"SET LOCAL hnsw.ef_search = {settings.HNSW_EF_SEARCH}")

        return await connection.fetch(
            """
            SELECT
                c.id,
                c.document_id,
                c.chunk_index,
                c.content,
                c.token_count,
                d.title AS document_title,
                d.document_type,
                1 - (c.embedding <=> $1::vector) AS similarity
            FROM document_chunks AS c
            JOIN documents AS d ON d.id = c.document_id
            WHERE c.user_id = $2
              AND d.processing_status = 'processed'
            ORDER BY c.embedding <=> $1::vector
            LIMIT $3
            """,
            vector,
            user_id,
            limit,
        )
