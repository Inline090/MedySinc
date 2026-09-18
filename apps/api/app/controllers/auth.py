from uuid import UUID

import asyncpg
from asyncpg.exceptions import UniqueViolationError
from fastapi import Request, Response
from jwt import InvalidTokenError

from app.core.cookies import (
    ACCESS_COOKIE,
    REFRESH_COOKIE,
    access_cookie_options,
    refresh_cookie_options,
)
from app.core.exceptions import AppError
from app.core.security import hash_password, verify_password_or_dummy
from app.core.tokens import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.repositories.users import create_user, find_user_by_email, find_user_by_id
from app.schemas.auth import LoginRequest, RegisterRequest


def _public_user(user: asyncpg.Record) -> dict[str, object]:
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "created_at": user["created_at"],
        "updated_at": user["updated_at"],
    }


def _set_auth_cookies(response: Response, user_id: UUID) -> None:
    response.set_cookie(ACCESS_COOKIE, create_access_token(user_id), **access_cookie_options())
    response.set_cookie(REFRESH_COOKIE, create_refresh_token(user_id), **refresh_cookie_options())


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")


async def register_user(payload: RegisterRequest) -> dict[str, object]:
    existing = await find_user_by_email(payload.email)

    if existing is not None:
        raise AppError("That email is already registered", 409)

    try:
        user = await create_user(
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
        )
    except UniqueViolationError as error:
        raise AppError("That email is already registered", 409) from error

    return {"user": _public_user(user)}


async def login_user(payload: LoginRequest, response: Response) -> dict[str, object]:
    user = await find_user_by_email(payload.email)

    password_matches = verify_password_or_dummy(
        payload.password,
        user["password_hash"] if user is not None else None,
    )

    if user is None or not password_matches:
        raise AppError("Invalid email or password", 401)

    _set_auth_cookies(response, user["id"])

    return {"user": _public_user(user)}


async def refresh_tokens(request: Request, response: Response) -> dict[str, object]:
    token = request.cookies.get(REFRESH_COOKIE)

    if token is None:
        raise AppError("Missing refresh token", 401)

    try:
        payload = decode_token(token)
    except InvalidTokenError as error:
        raise AppError("Invalid or expired refresh token", 401) from error

    if payload.get("type") != REFRESH_TOKEN_TYPE:
        raise AppError("Invalid or expired refresh token", 401)

    user_id = UUID(str(payload["sub"]))
    user = await find_user_by_id(user_id)

    if user is None:
        raise AppError("Invalid or expired refresh token", 401)

    _set_auth_cookies(response, user_id)

    return {"user": _public_user(user)}


async def logout_user(response: Response) -> dict[str, str]:
    _clear_auth_cookies(response)

    return {"message": "Logged out"}
