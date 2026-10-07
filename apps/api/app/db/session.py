"""The database connection pool."""

import asyncpg

from app.core.config import settings

_pool: asyncpg.Pool | None = None


async def connect() -> None:
    """Create the connection pool. Called once from the FastAPI lifespan."""

    global _pool
    _pool = await asyncpg.create_pool(
        dsn=settings.DATABASE_URL,
        min_size=1,
        max_size=10,
    )


async def disconnect() -> None:
    """Close the pool and drop the reference. Called from the lifespan on shutdown."""

    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    """Return the live connection pool."""

    if _pool is None:
        raise RuntimeError("database pool has not been initialised")
    return _pool
