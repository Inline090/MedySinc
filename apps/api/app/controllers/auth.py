from asyncpg.exceptions import UniqueViolationError

from app.core.exceptions import AppError
from app.core.security import hash_password
from app.repositories.users import create_user, find_user_by_email
from app.schemas.auth import RegisterRequest


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

    return {"user": dict(user)}
