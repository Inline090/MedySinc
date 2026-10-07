"""The medications feature: a list of every medicine found in a user's documents."""

from typing import Annotated

import asyncpg
from fastapi import Depends, Query

from app.middlewares.auth import get_current_user
from app.repositories.medicines import count_medicines_for_user, list_medicines_for_user


def medicine_row(row: asyncpg.Record) -> dict[str, object]:
    """Formats a medicine row to send to the client."""

    return {
        "id": row["id"],
        "document_id": row["document_id"],
        "document_title": row["document_title"],
        "hospital": row["hospital"],
        "medicine": row["medicine"],
        "dose": row["dose"],
        "frequency": row["frequency"],
        "prescribed_on": row["prescribed_on"],
        "notes": row["notes"],
    }


async def list_user_medicines(
    user: Annotated[asyncpg.Record, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, object]:
    """Lists all medicines found in the logged-in user's documents."""

    rows = await list_medicines_for_user(user_id=user["id"], limit=limit, offset=offset)
    total = await count_medicines_for_user(user["id"])

    return {
        "medicines": [medicine_row(row) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
