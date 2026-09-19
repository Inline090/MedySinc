from uuid import UUID

import asyncpg

from app.db.session import get_pool

_LIST_COLUMNS = """
    id,
    title,
    document_type,
    tags,
    notes,
    original_name,
    mime_type,
    size_bytes,
    processing_status,
    created_at,
    updated_at
"""

_DETAIL_COLUMNS = f"{_LIST_COLUMNS},\n    user_id,\n    storage_key,\n    extracted_text"


async def create_document(
    *,
    user_id: UUID,
    title: str,
    document_type: str,
    original_name: str,
    storage_key: str,
    mime_type: str,
    size_bytes: int,
    tags: list[str],
    notes: str | None = None,
) -> asyncpg.Record:
    pool = get_pool()

    return await pool.fetchrow(
        f"""
        INSERT INTO documents (
            user_id, title, document_type, original_name,
            storage_key, mime_type, size_bytes, tags, notes
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING {_DETAIL_COLUMNS}
        """,
        user_id,
        title,
        document_type,
        original_name,
        storage_key,
        mime_type,
        size_bytes,
        tags,
        notes,
    )


def _list_filters(
    user_id: UUID,
    document_type: str | None,
    tag: str | None,
    search: str | None,
) -> tuple[str, list[object]]:
    conditions = ["user_id = $1"]
    params: list[object] = [user_id]

    if document_type is not None:
        params.append(document_type)
        conditions.append(f"document_type = ${len(params)}")

    if tag is not None:
        params.append(tag)
        conditions.append(f"tags @> ARRAY[${len(params)}]::text[]")

    if search is not None:
        params.append(search)
        conditions.append(f"search_vector @@ websearch_to_tsquery('english', ${len(params)})")

    return " AND ".join(conditions), params


async def list_documents(
    *,
    user_id: UUID,
    limit: int,
    offset: int,
    document_type: str | None = None,
    tag: str | None = None,
    search: str | None = None,
) -> list[asyncpg.Record]:
    pool = get_pool()
    where, params = _list_filters(user_id, document_type, tag, search)

    params.extend([limit, offset])

    return await pool.fetch(
        f"""
        SELECT {_LIST_COLUMNS}
        FROM documents
        WHERE {where}
        ORDER BY created_at DESC
        LIMIT ${len(params) - 1} OFFSET ${len(params)}
        """,
        *params,
    )


async def count_documents(
    *,
    user_id: UUID,
    document_type: str | None = None,
    tag: str | None = None,
    search: str | None = None,
) -> int:
    pool = get_pool()
    where, params = _list_filters(user_id, document_type, tag, search)

    return await pool.fetchval(
        f"SELECT count(*) FROM documents WHERE {where}",
        *params,
    )


async def find_document_for_user(document_id: UUID, user_id: UUID) -> asyncpg.Record | None:
    pool = get_pool()

    return await pool.fetchrow(
        f"""
        SELECT {_DETAIL_COLUMNS}
        FROM documents
        WHERE id = $1 AND user_id = $2
        """,
        document_id,
        user_id,
    )


async def find_document_by_id(document_id: UUID) -> asyncpg.Record | None:
    pool = get_pool()

    return await pool.fetchrow(
        f"""
        SELECT {_DETAIL_COLUMNS}
        FROM documents
        WHERE id = $1
        """,
        document_id,
    )


async def delete_document(document_id: UUID, user_id: UUID) -> str | None:
    pool = get_pool()

    return await pool.fetchval(
        """
        DELETE FROM documents
        WHERE id = $1 AND user_id = $2
        RETURNING storage_key
        """,
        document_id,
        user_id,
    )
