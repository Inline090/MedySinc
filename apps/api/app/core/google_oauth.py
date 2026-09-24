import secrets
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.core.exceptions import AppError

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
SCOPE = "openid email profile"
TIMEOUT_SECONDS = 10.0


def new_state() -> str:
    return secrets.token_urlsafe(32)


def build_authorize_url(state: str) -> str:
    if not settings.GOOGLE_CLIENT_ID:
        raise AppError("Google sign-in is not configured", 503)

    query = urlencode(
        {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URL,
            "response_type": "code",
            "scope": SCOPE,
            "state": state,
            "prompt": "select_account",
        }
    )

    return f"{AUTHORIZE_URL}?{query}"


async def fetch_profile(code: str) -> dict[str, object]:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise AppError("Google sign-in is not configured", 503)

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        token_response = await client.post(
            TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URL,
                "grant_type": "authorization_code",
            },
        )

        if token_response.status_code != 200:
            raise AppError("Google rejected the sign-in attempt", 401)

        access_token = token_response.json().get("access_token")

        if not access_token:
            raise AppError("Google did not return an access token", 401)

        profile_response = await client.get(
            USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if profile_response.status_code != 200:
        raise AppError("Could not read the Google profile", 401)

    return profile_response.json()
