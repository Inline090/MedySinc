"""Queries for the document_medicines table."""

from uuid import UUID

import asyncpg

from app.db.session import get_pool

_LIST_COLUMNS = """
    m.id,
    m.document_id,
    m.hospital,
    m.medicine,
    m.dose,
    m.frequency,
    m.prescribed_on,
    m.notes,
    d.title AS document_title,
    d.created_at AS document_created_at
"""


async def replace_document_medicines(
    *,
    document_id: UUID,
    user_id: UUID,
    rows: list[dict[str, object]],
) -> None:
    """Store a document's medicines, replacing any it already had."""

    pool = get_pool()

    async with pool.acquire() as connection, connection.transaction():
        await connection.execute(
            "DELETE FROM document_medicines WHERE document_id = $1",
            document_id,
        )

        if not rows:
            return

        await connection.executemany(
            """
            INSERT INTO document_medicines (
                document_id, user_id, hospital, medicine,
                dose, frequency, prescribed_on, notes
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            [
                (
                    document_id,
                    user_id,
                    row.get("hospital"),
                    row.get("medicine"),
                    row.get("dose"),
                    row.get("frequency"),
                    row.get("prescribed_on"),
                    row.get("notes"),
                )
                for row in rows
            ],
        )


async def list_medicines_for_user(
    *,
    user_id: UUID,
    limit: int,
    offset: int,
) -> list[asyncpg.Record]:
    """List every medicine the user has, newest document first."""

    pool = get_pool()

    return await pool.fetch(
        f"""
        SELECT {_LIST_COLUMNS}
        FROM document_medicines AS m
        JOIN documents AS d ON d.id = m.document_id
        WHERE m.user_id = $1
        ORDER BY d.created_at DESC, m.medicine
        LIMIT $2 OFFSET $3
        """,
        user_id,
        limit,
        offset,
    )


async def count_medicines_for_user(user_id: UUID) -> int:
    """Count the medicines the user has."""

    pool = get_pool()

    return await pool.fetchval(
        "SELECT count(*) FROM document_medicines WHERE user_id = $1",
        user_id,
    )
