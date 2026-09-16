import asyncio
from pathlib import Path

from app.db.session import connect, disconnect, get_pool

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def run_migrations() -> list[str]:
    pool = get_pool()
    applied: list[str] = []

    async with pool.acquire() as connection:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                name TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

        rows = await connection.fetch("SELECT name FROM schema_migrations")
        already_applied = {row["name"] for row in rows}

        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in already_applied:
                continue

            async with connection.transaction():
                await connection.execute(path.read_text(encoding="utf-8"))
                await connection.execute(
                    "INSERT INTO schema_migrations (name) VALUES ($1)",
                    path.name,
                )

            applied.append(path.name)

    return applied


async def main() -> None:
    await connect()
    try:
        applied = await run_migrations()
    finally:
        await disconnect()

    if applied:
        for name in applied:
            print(f"applied {name}")
    else:
        print("database is up to date")


if __name__ == "__main__":
    asyncio.run(main())
