from uuid import UUID

import asyncpg

from app.db.session import get_pool


async def create_user(
    email: str,
    password_hash: str,
    full_name: str | None = None,
) -> asyncpg.Record:
    pool = get_pool()
    return await pool.fetchrow(
        """
        INSERT INTO users (email, password_hash, full_name)
        VALUES ($1, $2, $3)
        RETURNING id, email, full_name, created_at, updated_at
        """,
        email,
        password_hash,
        full_name,
    )


async def create_oauth_user(email: str, full_name: str | None = None) -> asyncpg.Record:
    pool = get_pool()
    return await pool.fetchrow(
        """
        INSERT INTO users (email, full_name)
        VALUES ($1, $2)
        RETURNING id, email, full_name, created_at, updated_at
        """,
        email,
        full_name,
    )


async def find_user_by_email(email: str) -> asyncpg.Record | None:
    pool = get_pool()
    return await pool.fetchrow(
        """
        SELECT id, email, password_hash, full_name, created_at, updated_at
        FROM users
        WHERE email = $1
        """,
        email,
    )


async def find_user_by_id(user_id: UUID) -> asyncpg.Record | None:
    pool = get_pool()
    return await pool.fetchrow(
        """
        SELECT id, email, full_name, created_at, updated_at
        FROM users
        WHERE id = $1
        """,
        user_id,
    )
