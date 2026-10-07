"""The main application entry point."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.embeddings import get_embeddings
from app.ai.reranker import get_reranker
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.db.session import connect, disconnect
from app.routers.auth import router as auth_router
from app.routers.documents import router as documents_router
from app.routers.healthcheck import router as healthcheck_router
from app.routers.medicines import router as medicines_router
from app.routers.qa import router as qa_router


async def warm_models() -> None:
    """Load the local models before the first request instead of during it."""

    with suppress(Exception):
        await get_embeddings().embed(["warm up"])

    if settings.RERANK_ENABLED:
        with suppress(Exception):
            await get_reranker().rerank("warm up", ["warm up"])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Open resources before serving and close them after."""

    await connect()

    warming = asyncio.create_task(warm_models())

    yield

    warming.cancel()
    await disconnect()


app = FastAPI(title="MedSync API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(healthcheck_router)
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(medicines_router)
app.include_router(qa_router)

register_exception_handlers(app)


@app.get("/")
async def root() -> dict[str, str]:
    """A trivial landing route, so hitting the host root is not a 404."""

    return {"message": "Welcome to MedSync API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=settings.PORT, reload=True)
