"""A sliding window rate limiter that uses PostgreSQL."""

import random
from collections.abc import Awaitable, Callable

from fastapi import Request

from app.core.config import settings
from app.core.exceptions import AppError
from app.db.session import get_pool

PRUNE_PROBABILITY = 0.01
RETENTION_HOURS = 1


def client_identifier(request: Request) -> str:
    """Identifies the client making the request."""

    if settings.TRUST_PROXY:
        forwarded = request.headers.get("x-forwarded-for")

        if forwarded:
            return forwarded.split(",")[0].strip()

    return request.client.host if request.client is not None else "unknown"


async def enforce(*, scope: str, identifier: str, limit: int, window_seconds: int) -> None:
    """Increments the request count and rejects it if it's too high."""

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

    window = await pool.fetchrow(
        """
        SELECT
            coalesce(previous.count, 0) AS previous_count,
            extract(epoch from now()) - extract(epoch from current.window_start) AS elapsed_seconds
        FROM rate_limits AS current
        LEFT JOIN rate_limits AS previous
            ON previous.scope = current.scope
           AND previous.identifier = current.identifier
           AND previous.window_start =
               current.window_start - make_interval(secs => $3)
        WHERE current.scope = $1
          AND current.identifier = $2
          AND current.window_start =
              to_timestamp(floor(extract(epoch from now()) / $3) * $3)
        """,
        scope,
        identifier,
        window_seconds,
    )

    if window is None:
        weighted = float(count)
    else:
        fraction = min(float(window["elapsed_seconds"]) / window_seconds, 1.0)
        weighted = float(window["previous_count"]) * (1 - fraction) + float(count)

    if random.random() < PRUNE_PROBABILITY:
        await pool.execute(
            "DELETE FROM rate_limits WHERE window_start < now() - make_interval(hours => $1::int)",
            RETENTION_HOURS,
        )

    if weighted > limit:
        # The wait is at most one window: after that the previous count is gone.
        raise AppError(f"Too many requests. Try again within {window_seconds} seconds.", 429)


def rate_limit(scope: str, limit: int, window_seconds: int = 60) -> Callable[..., Awaitable[None]]:
    """Creates a FastAPI dependency to enforce a specific rate limit."""

    async def dependency(request: Request) -> None:
        await enforce(
            scope=scope,
            identifier=client_identifier(request),
            limit=limit,
            window_seconds=window_seconds,
        )

    return dependency
