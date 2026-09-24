from app.core.config import settings

START = "/api/v1/auth/google/start"
CALLBACK = "/api/v1/auth/google/callback"
REGISTER = "/api/v1/auth/register"
ME = "/api/v1/auth/me"

EMAIL = "gina@example.com"
PASSWORD = "secret123"

PROFILE = {
    "sub": "google-subject-1",
    "email": EMAIL,
    "email_verified": True,
    "name": "Gina",
}


def _configure_google(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "test-client-secret")


def _stub_profile(monkeypatch, profile):
    async def fake_fetch_profile(code):
        assert code == "auth-code"
        return profile

    monkeypatch.setattr("app.controllers.auth.fetch_profile", fake_fetch_profile)


def _set_cookie_headers(response, name):
    return [item for item in response.headers.get_list("set-cookie") if item.startswith(f"{name}=")]


def _cookie_value(response, name):
    return _set_cookie_headers(response, name)[0].split(";")[0].split("=", 1)[1]


async def test_google_start_redirects_to_google_with_httponly_state(client, monkeypatch):
    _configure_google(monkeypatch)

    response = await client.get(START, follow_redirects=False)

    assert response.status_code == 303

    location = response.headers["location"]
    assert location.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "client_id=test-client-id" in location
    assert "state=" in location

    state_headers = _set_cookie_headers(response, "oauth_state")
    assert state_headers
    assert "HttpOnly" in state_headers[0]


async def test_google_start_reports_when_unconfigured(client, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", None)

    response = await client.get(START, follow_redirects=False)

    assert response.status_code == 503


async def test_google_callback_rejects_a_missing_state_cookie(client, monkeypatch):
    _configure_google(monkeypatch)

    response = await client.get(
        CALLBACK,
        params={"code": "auth-code", "state": "whatever"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].endswith("/sign-in?error=google")


async def test_google_callback_rejects_a_mismatched_state(client, monkeypatch):
    _configure_google(monkeypatch)
    client.cookies.set("oauth_state", "expected-state")

    response = await client.get(
        CALLBACK,
        params={"code": "auth-code", "state": "different-state"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].endswith("/sign-in?error=google")


async def test_google_callback_creates_user_and_sets_auth_cookies(client, monkeypatch):
    _configure_google(monkeypatch)
    _stub_profile(monkeypatch, PROFILE)
    client.cookies.set("oauth_state", "matching-state")

    response = await client.get(
        CALLBACK,
        params={"code": "auth-code", "state": "matching-state"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].endswith("/dashboard")

    cookies = response.headers.get_list("set-cookie")
    assert any(item.startswith("access_token=") and "HttpOnly" in item for item in cookies)
    assert any(item.startswith("refresh_token=") and "HttpOnly" in item for item in cookies)

    me = await client.get(ME)

    assert me.status_code == 200
    assert me.json()["user"]["email"] == EMAIL
    assert "password_hash" not in me.json()["user"]


async def test_google_callback_links_an_existing_verified_account(client, monkeypatch):
    _configure_google(monkeypatch)
    _stub_profile(monkeypatch, PROFILE)
    registered = await client.post(REGISTER, json={"email": EMAIL, "password": PASSWORD})

    client.cookies.set("oauth_state", "matching-state")

    response = await client.get(
        CALLBACK,
        params={"code": "auth-code", "state": "matching-state"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].endswith("/dashboard")

    me = await client.get(ME)

    assert me.json()["user"]["id"] == registered.json()["user"]["id"]


async def test_google_callback_refuses_to_link_an_unverified_email(client, monkeypatch):
    _configure_google(monkeypatch)
    _stub_profile(monkeypatch, {**PROFILE, "email_verified": False})
    await client.post(REGISTER, json={"email": EMAIL, "password": PASSWORD})

    client.cookies.set("oauth_state", "matching-state")

    response = await client.get(
        CALLBACK,
        params={"code": "auth-code", "state": "matching-state"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].endswith("/sign-in?error=google")
    assert not _set_cookie_headers(response, "access_token")
