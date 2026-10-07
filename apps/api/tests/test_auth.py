REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"
ME = "/api/v1/auth/me"

EMAIL = "ann@example.com"
PASSWORD = "secret123"


async def _register(client, **overrides):
    """Registers a test user with default or overridden details."""
    payload = {"email": EMAIL, "password": PASSWORD, "full_name": "Ann", **overrides}
    return await client.post(REGISTER, json=payload)


async def _login(client, **overrides):
    """Logs in a test user with default or overridden details."""
    payload = {"email": EMAIL, "password": PASSWORD, **overrides}
    return await client.post(LOGIN, json=payload)


def _cookie(response, name):
    """Gets the value of a specific cookie from the response headers."""
    header = next(
        item for item in response.headers.get_list("set-cookie") if item.startswith(f"{name}=")
    )
    return header.split(";")[0].split("=", 1)[1]


async def test_register_creates_user_without_exposing_hash(client):
    """Checks that registration returns the user details but not the password hash."""
    response = await _register(client)

    assert response.status_code == 201

    user = response.json()["user"]

    assert user["email"] == EMAIL
    assert "password_hash" not in user


async def test_register_rejects_duplicate_email(client):
    """Checks that you can't register twice with the same email."""
    await _register(client)

    response = await _register(client)

    assert response.status_code == 409


async def test_register_normalises_email_case(client):
    """Checks that email matching is case-insensitive during registration."""
    await _register(client)

    response = await _register(client, email="ANN@Example.COM")

    assert response.status_code == 409


async def test_register_rejects_short_password(client):
    """Checks that passwords must meet the minimum length requirement."""
    response = await _register(client, password="short")

    assert response.status_code == 422


async def test_login_sets_httponly_cookies(client):
    """Checks that logging in sets secure HTTP-only cookies for tokens."""
    await _register(client)

    response = await _login(client)

    assert response.status_code == 200
    assert "password_hash" not in response.json()["user"]

    cookies = response.headers.get_list("set-cookie")

    assert any(item.startswith("access_token=") and "HttpOnly" in item for item in cookies)
    assert any(item.startswith("refresh_token=") and "HttpOnly" in item for item in cookies)


async def test_login_rejects_wrong_password(client):
    """Checks that logging in with an incorrect password fails."""
    await _register(client)

    response = await _login(client, password="wrongpassword")

    assert response.status_code == 401


async def test_login_does_not_reveal_whether_email_exists(client):
    """Checks that login errors don't indicate if an email is registered or not."""
    await _register(client)

    unknown_email = await _login(client, email="nobody@example.com")
    wrong_password = await _login(client, password="wrongpassword")

    assert unknown_email.status_code == 401
    assert wrong_password.status_code == 401
    assert unknown_email.json() == wrong_password.json()


async def test_me_requires_authentication(client):
    """Checks that the /me endpoint requires a logged-in user."""
    response = await client.get(ME)

    assert response.status_code == 401


async def test_me_returns_current_user(client):
    """Checks that the /me endpoint returns the logged-in user's details."""
    await _register(client)
    await _login(client)

    response = await client.get(ME)

    assert response.status_code == 200
    assert response.json()["user"]["email"] == EMAIL


async def test_me_rejects_a_refresh_token_used_as_access_token(client):
    """Checks that a refresh token cannot be used to access protected endpoints."""
    await _register(client)
    login = await _login(client)

    client.cookies.set("access_token", _cookie(login, "refresh_token"))

    response = await client.get(ME)

    assert response.status_code == 401


async def test_refresh_requires_a_refresh_token(client):
    """Checks that the refresh endpoint requires a valid refresh token."""
    response = await client.post(REFRESH)

    assert response.status_code == 401


async def test_refresh_issues_new_cookies(client):
    """Checks that refreshing issues a new access token."""
    await _register(client)
    await _login(client)

    response = await client.post(REFRESH)

    assert response.status_code == 200
    assert any(item.startswith("access_token=") for item in response.headers.get_list("set-cookie"))


async def test_logout_clears_auth_cookies(client):
    """Checks that logging out removes the token cookies."""
    await _register(client)
    await _login(client)

    response = await client.post(LOGOUT)

    assert response.status_code == 200

    cleared = response.headers.get_list("set-cookie")

    assert any('access_token=""' in item for item in cleared)
    assert any('refresh_token=""' in item for item in cleared)
