import pytest

from app.core.exceptions import AppError
from app.core.rate_limit import enforce
from app.db.session import get_pool

LOGIN = "/api/v1/auth/login"
REGISTER = "/api/v1/auth/register"

EMAIL = "ratelimit@example.com"
PASSWORD = "secret123"

WINDOW = 60


async def test_login_is_rate_limited_per_client(client):
    """Checks that the login endpoint blocks requests after 10 tries."""
    await client.post(REGISTER, json={"email": EMAIL, "password": PASSWORD})

    statuses = []

    for _ in range(11):
        response = await client.post(LOGIN, json={"email": EMAIL, "password": PASSWORD})
        statuses.append(response.status_code)

    assert statuses[:10] == [200] * 10
    assert statuses[10] == 429


async def test_register_is_rate_limited_per_client(client):
    """Checks that the registration endpoint blocks requests after 5 tries."""
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
    """Checks that a blocked login request does not issue any tokens."""
    await client.post(REGISTER, json={"email": EMAIL, "password": PASSWORD})

    for _ in range(10):
        await client.post(LOGIN, json={"email": EMAIL, "password": PASSWORD})

    blocked = await client.post(LOGIN, json={"email": EMAIL, "password": PASSWORD})

    assert blocked.status_code == 429
    assert "access_token" not in blocked.headers.get_list("set-cookie")


async def _put_count_in_an_older_window(
    scope: str,
    identifier: str,
    windows_ago: int,
    count: int,
) -> None:
    """Writes a rate-limit row into a window that has already passed."""

    await get_pool().execute(
        """
        INSERT INTO rate_limits (scope, identifier, window_start, count)
        VALUES (
            $1,
            $2,
            to_timestamp(floor(extract(epoch from now()) / $4) * $4)
                - make_interval(secs => $4 * $3),
            $5
        )
        """,
        scope,
        identifier,
        windows_ago,
        WINDOW,
        count,
    )


async def test_the_previous_window_still_counts(client):
    """The window before this one is still measured against us."""

    await _put_count_in_an_older_window("test:sliding", "same-client", 1, 10)

    with pytest.raises(AppError) as raised:
        await enforce(
            scope="test:sliding",
            identifier="same-client",
            limit=1,
            window_seconds=WINDOW,
        )

    assert "Too many requests" in str(raised.value)


async def test_a_window_two_minutes_back_is_ignored(client):
    """The weighting fades, and anything older than one window is gone."""

    await _put_count_in_an_older_window("test:sliding:old", "same-client", 2, 10)

    await enforce(
        scope="test:sliding:old",
        identifier="same-client",
        limit=1,
        window_seconds=WINDOW,
    )
