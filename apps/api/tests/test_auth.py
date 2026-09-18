REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"
ME = "/api/v1/auth/me"

EMAIL = "ann@example.com"
PASSWORD = "secret123"


async def _register(client, **overrides):
    payload = {"email": EMAIL, "password": PASSWORD, "full_name": "Ann", **overrides}
    return await client.post(REGISTER, json=payload)


async def _login(client, **overrides):
    payload = {"email": EMAIL, "password": PASSWORD, **overrides}
    return await client.post(LOGIN, json=payload)


def _cookie(response, name):
    header = next(
        item for item in response.headers.get_list("set-cookie") if item.startswith(f"{name}=")
    )
    return header.split(";")[0].split("=", 1)[1]


async def test_register_creates_user_without_exposing_hash(client):
    response = await _register(client)

    assert response.status_code == 201

    user = response.json()["user"]

    assert user["email"] == EMAIL
    assert "password_hash" not in user


async def test_register_rejects_duplicate_email(client):
    await _register(client)

    response = await _register(client)

    assert response.status_code == 409


async def test_register_normalises_email_case(client):
    await _register(client)

    response = await _register(client, email="ANN@Example.COM")

    assert response.status_code == 409


async def test_register_rejects_short_password(client):
    response = await _register(client, password="short")

    assert response.status_code == 422


async def test_login_sets_httponly_cookies(client):
    await _register(client)

    response = await _login(client)

    assert response.status_code == 200
    assert "password_hash" not in response.json()["user"]

    cookies = response.headers.get_list("set-cookie")

    assert any(item.startswith("access_token=") and "HttpOnly" in item for item in cookies)
    assert any(item.startswith("refresh_token=") and "HttpOnly" in item for item in cookies)


async def test_login_rejects_wrong_password(client):
    await _register(client)

    response = await _login(client, password="wrongpassword")

    assert response.status_code == 401


async def test_login_does_not_reveal_whether_email_exists(client):
    await _register(client)

    unknown_email = await _login(client, email="nobody@example.com")
    wrong_password = await _login(client, password="wrongpassword")

    assert unknown_email.status_code == 401
    assert wrong_password.status_code == 401
    assert unknown_email.json() == wrong_password.json()


async def test_me_requires_authentication(client):
    response = await client.get(ME)

    assert response.status_code == 401


async def test_me_returns_current_user(client):
    await _register(client)
    await _login(client)

    response = await client.get(ME)

    assert response.status_code == 200
    assert response.json()["user"]["email"] == EMAIL


async def test_me_rejects_a_refresh_token_used_as_access_token(client):
    await _register(client)
    login = await _login(client)

    client.cookies.set("access_token", _cookie(login, "refresh_token"))

    response = await client.get(ME)

    assert response.status_code == 401


async def test_refresh_requires_a_refresh_token(client):
    response = await client.post(REFRESH)

    assert response.status_code == 401


async def test_refresh_issues_new_cookies(client):
    await _register(client)
    await _login(client)

    response = await client.post(REFRESH)

    assert response.status_code == 200
    assert any(item.startswith("access_token=") for item in response.headers.get_list("set-cookie"))


async def test_logout_clears_auth_cookies(client):
    await _register(client)
    await _login(client)

    response = await client.post(LOGOUT)

    assert response.status_code == 200

    cleared = response.headers.get_list("set-cookie")

    assert any('access_token=""' in item for item in cleared)
    assert any('refresh_token=""' in item for item in cleared)
