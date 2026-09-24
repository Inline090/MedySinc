import random
from collections.abc import Awaitable, Callable

from fastapi import Request

from app.core.exceptions import AppError
from app.db.session import get_pool

PRUNE_PROBABILITY = 0.01
RETENTION_HOURS = 1


def client_identifier(request: Request) -> str:
    return request.client.host if request.client is not None else "unknown"


async def enforce(*, scope: str, identifier: str, limit: int, window_seconds: int) -> None:
    pool = get_pool()

    count = await pool.fetchval(
        """
        INSERT INTO rate_limits (scope, identifier, window_start, count)
        VALUES (
            $1,
            $2,
            to_timestamp(floor(extract(epoch from now()) / $3) * $3),
            1
        )
        ON CONFLICT (scope, identifier, window_start)
        DO UPDATE SET count = rate_limits.count + 1
        RETURNING count
        """,
        scope,
        identifier,
        window_seconds,
    )

    if random.random() < PRUNE_PROBABILITY:
        await pool.execute(
            "DELETE FROM rate_limits WHERE window_start < now() - make_interval(hours => $1::int)",
            RETENTION_HOURS,
        )

    if count > limit:
        raise AppError(f"Too many requests. Try again in {window_seconds} seconds.", 429)


def rate_limit(scope: str, limit: int, window_seconds: int = 60) -> Callable[..., Awaitable[None]]:
    async def dependency(request: Request) -> None:
        await enforce(
            scope=scope,
            identifier=client_identifier(request),
            limit=limit,
            window_seconds=window_seconds,
        )

    return dependency
