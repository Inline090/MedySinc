from uuid import UUID

import asyncpg

from app.db.session import get_pool

PROVIDER_GOOGLE = "google"


async def find_identity(provider: str, provider_subject: str) -> asyncpg.Record | None:
    pool = get_pool()

    return await pool.fetchrow(
        """
        SELECT user_id
        FROM user_identities
        WHERE provider = $1 AND provider_subject = $2
        """,
        provider,
        provider_subject,
    )


async def create_identity(*, user_id: UUID, provider: str, provider_subject: str) -> None:
    pool = get_pool()

    await pool.execute(
        """
        INSERT INTO user_identities (user_id, provider, provider_subject)
        VALUES ($1, $2, $3)
        ON CONFLICT (provider, provider_subject) DO NOTHING
        """,
        user_id,
        provider,
        provider_subject,
    )
