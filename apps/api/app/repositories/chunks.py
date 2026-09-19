from uuid import UUID

import asyncpg

from app.core.config import settings
from app.db.session import get_pool


def _to_vector(embedding: list[float]) -> str:
    return "[" + ",".join(str(value) for value in embedding) + "]"


_SEARCH_COLUMNS = """
    c.id,
    c.document_id,
    c.chunk_index,
    c.content,
    c.token_count,
    d.title AS document_title,
    d.document_type,
    1 - (c.embedding <=> $1::vector) AS similarity
"""


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


async def search_chunks_by_vector(
    *,
    user_id: UUID,
    embedding: list[float],
    limit: int,
) -> list[asyncpg.Record]:
    pool = get_pool()

    async with pool.acquire() as connection, connection.transaction():
        await connection.execute(f"SET LOCAL hnsw.ef_search = {settings.HNSW_EF_SEARCH}")

        return await connection.fetch(
            f"""
            SELECT {_SEARCH_COLUMNS}
            FROM document_chunks AS c
            JOIN documents AS d ON d.id = c.document_id
            WHERE c.user_id = $2
              AND d.processing_status = 'processed'
            ORDER BY c.embedding <=> $1::vector
            LIMIT $3
            """,
            _to_vector(embedding),
            user_id,
            limit,
        )


async def search_chunks_by_text(
    *,
    user_id: UUID,
    embedding: list[float],
    query: str,
    limit: int,
) -> list[asyncpg.Record]:
    pool = get_pool()

    return await pool.fetch(
        f"""
        SELECT {_SEARCH_COLUMNS},
            ts_rank(c.tsv, websearch_to_tsquery('english', $3)) AS rank
        FROM document_chunks AS c
        JOIN documents AS d ON d.id = c.document_id
        WHERE c.user_id = $2
          AND d.processing_status = 'processed'
          AND c.tsv @@ websearch_to_tsquery('english', $3)
        ORDER BY rank DESC
        LIMIT $4
        """,
        _to_vector(embedding),
        user_id,
        query,
        limit,
    )
