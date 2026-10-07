"""The healthcheck endpoint."""

from app.core.exceptions import AppError
from app.db.session import get_pool


async def health_check() -> dict[str, str]:
    """Checks if the web server and database are working."""

    try:
        await get_pool().fetchval("SELECT 1")
    except Exception as error:
        raise AppError("Database is unreachable", 503) from error

    return {"message": "Server is running"}
