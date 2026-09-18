from uuid import UUID

import asyncpg
from fastapi import Cookie
from jwt import InvalidTokenError

from app.core.cookies import ACCESS_COOKIE
from app.core.exceptions import AppError
from app.core.tokens import ACCESS_TOKEN_TYPE, decode_token
from app.repositories.users import find_user_by_id


async def get_current_user(
    access_token: str | None = Cookie(default=None, alias=ACCESS_COOKIE),
) -> asyncpg.Record:
    if access_token is None:
        raise AppError("Not authenticated", 401)

    try:
        payload = decode_token(access_token)
    except InvalidTokenError as error:
        raise AppError("Invalid or expired session", 401) from error

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise AppError("Invalid or expired session", 401)

    user = await find_user_by_id(UUID(str(payload["sub"])))

    if user is None:
        raise AppError("Invalid or expired session", 401)

    return user
