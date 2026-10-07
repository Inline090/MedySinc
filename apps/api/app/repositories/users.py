"""Queries against the users table."""

from uuid import UUID

import asyncpg

from app.db.session import get_pool


async def create_user(
    email: str,
    password_hash: str,
    full_name: str | None = None,
) -> asyncpg.Record:
    """Inserts a new user with a password."""

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
    """Insert a new user who signed in with an external provider."""

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
    """Looks up a user by email and returns their password hash."""

    pool = get_pool()
    return await pool.fetchrow(
        """
        SELECT id, email, password_hash, full_name, token_version, created_at, updated_at
        FROM users
        WHERE email = $1
        """,
        email,
    )


async def find_user_by_id(user_id: UUID) -> asyncpg.Record | None:
    """Looks up an authenticated user by their ID."""

    pool = get_pool()
    return await pool.fetchrow(
        """
        SELECT id, email, full_name, token_version, created_at, updated_at
        FROM users
        WHERE id = $1
        """,
        user_id,
    )


async def bump_token_version(user_id: UUID) -> None:
    """Increments a user's token version to invalidate all their active sessions."""

    pool = get_pool()

    await pool.execute(
        """
        UPDATE users
        SET token_version = token_version + 1, updated_at = NOW()
        WHERE id = $1
        """,
        user_id,
    )
