"""Queries against the documents table."""

from uuid import UUID

import asyncpg

from app.db.session import get_pool

_LIST_COLUMNS = """
    id,
    title,
    notes,
    original_name,
    mime_type,
    size_bytes,
    processing_status,
    created_at,
    updated_at
"""

_DETAIL_COLUMNS = (
    f"{_LIST_COLUMNS},\n    user_id,\n    storage_key,\n    extracted_text,\n"
    f"    summary,\n    summary_model"
)


async def create_document(
    *,
    user_id: UUID,
    title: str,
    original_name: str,
    storage_key: str,
    mime_type: str,
    size_bytes: int,
    content_hash: str,
    notes: str | None = None,
) -> asyncpg.Record:
    """Inserts a document record for an uploaded file that is already stored."""

    pool = get_pool()

    return await pool.fetchrow(
        f"""
        INSERT INTO documents (
            user_id, title, original_name,
            storage_key, mime_type, size_bytes, notes, content_hash
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING {_DETAIL_COLUMNS}
        """,
        user_id,
        title,
        original_name,
        storage_key,
        mime_type,
        size_bytes,
        notes,
        content_hash,
    )


async def find_document_by_content_hash(
    user_id: UUID,
    content_hash: str,
) -> asyncpg.Record | None:
    """Look for an existing upload of the same bytes by the same user."""

    pool = get_pool()

    return await pool.fetchrow(
        f"""
        SELECT {_DETAIL_COLUMNS}
        FROM documents
        WHERE user_id = $1 AND content_hash = $2
        """,
        user_id,
        content_hash,
    )


async def list_documents(
    *,
    user_id: UUID,
    limit: int,
    offset: int,
) -> list[asyncpg.Record]:
    """Lists a user's documents, starting with the newest."""

    pool = get_pool()

    return await pool.fetch(
        f"""
        SELECT {_LIST_COLUMNS}
        FROM documents
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
        """,
        user_id,
        limit,
        offset,
    )


async def count_documents(
    *,
    user_id: UUID,
) -> int:
    """Count one user's documents."""

    pool = get_pool()

    return await pool.fetchval(
        """
        SELECT count(*) FROM documents
        WHERE user_id = $1
        """,
        user_id,
    )


async def find_document_for_user(document_id: UUID, user_id: UUID) -> asyncpg.Record | None:
    """Fetch one document, but only if it belongs to this user."""

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
    """Fetch a document by id alone, with NO user scoping."""

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
    """Deletes a document and returns its storage key so the file can be removed."""

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


async def update_document_processing(
    document_id: UUID,
    *,
    status: str,
    extracted_text: str | None = None,
    error: str | None = None,
) -> None:
    """Move a document through its processing states."""

    pool = get_pool()

    await pool.execute(
        """
        UPDATE documents
        SET processing_status = $2,
            processing_error = $3,
            extracted_text = coalesce($4, extracted_text),
            updated_at = NOW()
        WHERE id = $1
        """,
        document_id,
        status,
        error,
        extracted_text,
    )


async def update_document_metadata(
    document_id: UUID,
    user_id: UUID,
    *,
    title: str | None = None,
    notes: str | None = None,
) -> asyncpg.Record | None:
    """Change a document's title or notes, if it belongs to this user."""

    pool = get_pool()

    return await pool.fetchrow(
        f"""
        UPDATE documents
        SET title = coalesce($3, title),
            notes = coalesce($4, notes),
            updated_at = NOW()
        WHERE id = $1 AND user_id = $2
        RETURNING {_DETAIL_COLUMNS}
        """,
        document_id,
        user_id,
        title,
        notes,
    )


async def update_document_summary(document_id: UUID, *, summary: str, model: str) -> None:
    """Store a generated summary alongside the model that produced it."""

    pool = get_pool()

    await pool.execute(
        """
        UPDATE documents
        SET summary = $2, summary_model = $3, updated_at = NOW()
        WHERE id = $1
        """,
        document_id,
        summary,
        model,
    )
