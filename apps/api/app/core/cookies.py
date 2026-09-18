from typing import Any

from app.core.config import settings

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def _options(max_age: int) -> dict[str, Any]:
    return {
        "httponly": True,
        "samesite": "lax",
        "secure": settings.ENVIRONMENT == "production",
        "max_age": max_age,
        "path": "/",
    }


def access_cookie_options() -> dict[str, Any]:
    return _options(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)


def refresh_cookie_options() -> dict[str, Any]:
    return _options(settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
