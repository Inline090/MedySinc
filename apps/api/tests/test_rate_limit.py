LOGIN = "/api/v1/auth/login"
REGISTER = "/api/v1/auth/register"

EMAIL = "ratelimit@example.com"
PASSWORD = "secret123"


async def test_login_is_rate_limited_per_client(client):
    await client.post(REGISTER, json={"email": EMAIL, "password": PASSWORD})

    statuses = []

    for _ in range(11):
        response = await client.post(LOGIN, json={"email": EMAIL, "password": PASSWORD})
        statuses.append(response.status_code)

    assert statuses[:10] == [200] * 10
    assert statuses[10] == 429


async def test_register_is_rate_limited_per_client(client):
    statuses = []

    for index in range(6):
        response = await client.post(
            REGISTER,
            json={"email": f"limit{index}@example.com", "password": PASSWORD},
        )
        statuses.append(response.status_code)

    assert statuses[:5] == [201] * 5
    assert statuses[5] == 429


async def test_a_rate_limited_login_is_not_authenticated(client):
    await client.post(REGISTER, json={"email": EMAIL, "password": PASSWORD})

    for _ in range(10):
        await client.post(LOGIN, json={"email": EMAIL, "password": PASSWORD})

    blocked = await client.post(LOGIN, json={"email": EMAIL, "password": PASSWORD})

    assert blocked.status_code == 429
    assert "access_token" not in blocked.headers.get_list("set-cookie")
