"""Request shapes for the auth endpoints."""

from pydantic import BaseModel, EmailStr, Field, field_validator


class EmailPayload(BaseModel):
    """Base for any request that carries an email address."""

    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Trim and lowercase an email address before it is used."""

        return value.strip().lower()


class RegisterRequest(EmailPayload):
    """Body of POST /api/v1/auth/register."""

    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class LoginRequest(EmailPayload):
    """Body of POST /api/v1/auth/login."""

    password: str
