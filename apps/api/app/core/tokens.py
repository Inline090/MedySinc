"""Creates and decodes JSON Web Tokens (JWTs) for auth."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt

from app.core.config import settings

ALGORITHM = "HS256"

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def _create_token(
    subject: UUID,
    token_type: str,
    expires_delta: timedelta,
    token_version: int = 0,
) -> str:
    """Creates and signs a single JWT. Used by both access and refresh tokens."""

    issued_at = datetime.now(UTC)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "ver": token_version,
        "iat": issued_at,
        "exp": issued_at + expires_delta,
    }

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_access_token(user_id: UUID, token_version: int = 0) -> str:
    """Creates a short-lived access token."""

    return _create_token(
        user_id,
        ACCESS_TOKEN_TYPE,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_version,
    )


def create_refresh_token(user_id: UUID, token_version: int = 0) -> str:
    """Creates a long-lived refresh token."""

    return _create_token(
        user_id,
        REFRESH_TOKEN_TYPE,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_version,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Verifies a token and returns its data."""

    return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])


def token_version_of(payload: dict[str, Any]) -> int:
    """Gets the token version from the token data. Defaults to 0."""

    return int(payload.get("ver", 0))
