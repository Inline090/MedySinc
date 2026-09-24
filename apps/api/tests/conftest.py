import asyncio
import os

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

ADMIN_DSN = "postgresql://postgres:postgres@localhost:5434/postgres"
TEST_DSN = "postgresql://postgres:postgres@localhost:5434/medsync_test"

os.environ.setdefault("DATABASE_URL", TEST_DSN)


async def _prepare_database() -> None:
    admin = await asyncpg.connect(ADMIN_DSN)

    try:
        await admin.execute("DROP DATABASE IF EXISTS medsync_test WITH (FORCE)")
        await admin.execute("CREATE DATABASE medsync_test")
    finally:
        await admin.close()

    from app.db.migrate import run_migrations
    from app.db.session import connect, disconnect

    await connect()

    try:
        await run_migrations()
    finally:
        await disconnect()


@pytest.fixture(scope="session", autouse=True)
def prepared_database() -> None:
    asyncio.run(_prepare_database())


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    from app.db.session import connect, disconnect, get_pool
    from app.main import app

    await connect()

    try:
        await get_pool().execute("TRUNCATE users, rate_limits CASCADE")

        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as http_client:
            yield http_client
    finally:
        await disconnect()
