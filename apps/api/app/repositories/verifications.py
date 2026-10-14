"""Queries against the email_verifications table."""

from uuid import UUID

import asyncpg

from app.db.session import get_pool


async def replace_code(user_id: UUID, email: str, code: str, ttl_minutes: int) -> None:
    """Stores a fresh code, retiring any code the user has not used yet."""

    pool = get_pool()

    await pool.execute(
        """
        UPDATE email_verifications
        SET used_at = NOW()
        WHERE user_id = $1 AND used_at IS NULL
        """,
        user_id,
    )

    await pool.execute(
        """
        INSERT INTO email_verifications (user_id, email, code, expires_at)
        VALUES ($1, $2, $3, NOW() + make_interval(mins => $4))
        """,
        user_id,
        email,
        code,
        ttl_minutes,
    )


async def find_live_code(user_id: UUID) -> asyncpg.Record | None:
    """Gets the newest code that has not been used or expired."""

    pool = get_pool()

    return await pool.fetchrow(
        """
        SELECT id, code, attempts
        FROM email_verifications
        WHERE user_id = $1 AND used_at IS NULL AND expires_at > NOW()
        ORDER BY created_at DESC
        LIMIT 1
        """,
        user_id,
    )


async def record_failed_attempt(verification_id: UUID) -> int:
    """Counts a wrong guess and returns the new attempt total."""

    pool = get_pool()

    return await pool.fetchval(
        """
        UPDATE email_verifications
        SET attempts = attempts + 1
        WHERE id = $1
        RETURNING attempts
        """,
        verification_id,
    )


async def mark_code_used(verification_id: UUID) -> None:
    """Retires a code so it cannot be replayed."""

    pool = get_pool()

    await pool.execute(
        "UPDATE email_verifications SET used_at = NOW() WHERE id = $1",
        verification_id,
    )


async def count_recent_codes(user_id: UUID) -> int:
    """Counts how many codes this user asked for in the last hour."""

    pool = get_pool()

    return await pool.fetchval(
        """
        SELECT COUNT(*)
        FROM email_verifications
        WHERE user_id = $1 AND created_at > NOW() - INTERVAL '1 hour'
        """,
        user_id,
    )
