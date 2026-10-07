"""Cookie names and security settings for access and refresh tokens."""

from typing import Any

from app.core.config import settings

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"

REFRESH_COOKIE_PATH = "/api/v1/auth/refresh"


def _options(max_age: int, path: str = "/") -> dict[str, Any]:
    """Creates the standard cookie settings used by both tokens."""

    return {
        "httponly": True,
        "samesite": "lax",
        "secure": settings.ENVIRONMENT == "production",
        "max_age": max_age,
        "path": path,
    }


def access_cookie_options() -> dict[str, Any]:
    """Gets the cookie settings for the access token."""

    return _options(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)


def refresh_cookie_options() -> dict[str, Any]:
    """Gets the cookie settings for the refresh token."""

    return _options(
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        REFRESH_COOKIE_PATH,
    )
