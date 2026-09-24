import secrets
from typing import Annotated
from uuid import UUID

import asyncpg
from asyncpg.exceptions import UniqueViolationError
from fastapi import Depends, Request, Response
from fastapi.responses import RedirectResponse
from jwt import InvalidTokenError

from app.core.config import settings
from app.core.cookies import (
    ACCESS_COOKIE,
    REFRESH_COOKIE,
    access_cookie_options,
    refresh_cookie_options,
)
from app.core.exceptions import AppError
from app.core.google_oauth import build_authorize_url, fetch_profile, new_state
from app.core.security import hash_password, verify_password_or_dummy
from app.core.tokens import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.middlewares.auth import get_current_user
from app.repositories.identities import PROVIDER_GOOGLE, create_identity, find_identity
from app.repositories.users import (
    create_oauth_user,
    create_user,
    find_user_by_email,
    find_user_by_id,
)
from app.schemas.auth import LoginRequest, RegisterRequest

OAUTH_STATE_COOKIE = "oauth_state"
OAUTH_STATE_MAX_AGE = 600


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


async def read_current_user(
    user: Annotated[asyncpg.Record, Depends(get_current_user)],
) -> dict[str, object]:
    return {"user": _public_user(user)}


async def google_start() -> RedirectResponse:
    state = new_state()
    response = RedirectResponse(build_authorize_url(state), status_code=303)

    response.set_cookie(
        OAUTH_STATE_COOKIE,
        state,
        httponly=True,
        samesite="lax",
        secure=settings.ENVIRONMENT == "production",
        max_age=OAUTH_STATE_MAX_AGE,
        path="/",
    )

    return response


async def _user_from_google_profile(profile: dict[str, object]) -> asyncpg.Record:
    subject = str(profile.get("sub") or "")
    email = str(profile.get("email") or "").strip().lower()

    if not subject or not email:
        raise AppError("Google did not return an email address", 401)

    identity = await find_identity(PROVIDER_GOOGLE, subject)

    if identity is not None:
        user = await find_user_by_id(identity["user_id"])

        if user is None:
            raise AppError("Account no longer exists", 401)

        return user

    existing = await find_user_by_email(email)

    if existing is not None:
        # Linking by email is only safe when Google asserts the address is verified.
        if not profile.get("email_verified"):
            raise AppError("That email is already registered", 409)

        await create_identity(
            user_id=existing["id"],
            provider=PROVIDER_GOOGLE,
            provider_subject=subject,
        )

        return existing

    name = profile.get("name")
    user = await create_oauth_user(email=email, full_name=str(name) if name else None)

    await create_identity(
        user_id=user["id"],
        provider=PROVIDER_GOOGLE,
        provider_subject=subject,
    )

    return user


async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    failure = RedirectResponse(f"{settings.FRONTEND_URL}/sign-in?error=google", status_code=303)

    if error or not code or not state:
        return failure

    expected = request.cookies.get(OAUTH_STATE_COOKIE)

    if expected is None or not secrets.compare_digest(expected, state):
        return failure

    try:
        user = await _user_from_google_profile(await fetch_profile(code))
    except AppError:
        return failure

    response = RedirectResponse(f"{settings.FRONTEND_URL}/dashboard", status_code=303)
    _set_auth_cookies(response, user["id"])
    response.delete_cookie(OAUTH_STATE_COOKIE, path="/")

    return response
