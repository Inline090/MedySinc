from uuid import UUID, uuid4

import pymupdf
from httpx import AsyncClient

from app.ai.retrieval import Retrieval
from app.db.session import get_pool
from app.repositories.answers import (
    clear_answers_for_user,
    find_cached_answer,
    question_fingerprint,
    save_answer,
)

ASK = "/api/v1/ask"
REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
ME = "/api/v1/auth/me"
UPLOAD = "/api/v1/documents"

EMAIL = "cache@example.com"
PASSWORD = "secret123"


async def _seed_user(email: str) -> UUID:
    return await get_pool().fetchval(
        "INSERT INTO users (email, password_hash) VALUES ($1, 'x') RETURNING id",
        email,
    )


def _png() -> bytes:
    document = pymupdf.open()
    page = document.new_page(width=200, height=100)
    page.insert_text((20, 50), "Paracetamol", fontsize=16)
    data = page.get_pixmap(dpi=120).tobytes("png")
    document.close()

    return data


def test_question_fingerprint_ignores_case_and_whitespace():
    assert question_fingerprint("When was  Dolo taken?") == question_fingerprint(
        "when was dolo taken?"
    )


async def test_a_saved_answer_can_be_read_back(client: AsyncClient):
    user_id = await _seed_user("cache-read@example.com")

    await save_answer(
        user_id=user_id,
        question="when was dolo taken",
        answer="At 7 PM.",
        sources=[{"document_title": "rx"}],
        model="gemini-2.5-flash",
    )

    row = await find_cached_answer(user_id=user_id, question="WHEN WAS  dolo taken", ttl_hours=24)

    assert row is not None
    assert row["answer"] == "At 7 PM."


async def test_an_expired_answer_is_ignored(client: AsyncClient):
    user_id = await _seed_user("cache-expired@example.com")

    await save_answer(user_id=user_id, question="q", answer="a", sources=[], model=None)
    await get_pool().execute("UPDATE answer_cache SET created_at = NOW() - INTERVAL '48 hours'")

    assert await find_cached_answer(user_id=user_id, question="q", ttl_hours=24) is None


async def test_clearing_removes_only_that_users_answers(client: AsyncClient):
    mine = await _seed_user("cache-mine@example.com")
    theirs = await _seed_user("cache-theirs@example.com")

    await save_answer(user_id=mine, question="q", answer="mine", sources=[], model=None)
    await save_answer(user_id=theirs, question="q", answer="theirs", sources=[], model=None)

    await clear_answers_for_user(mine)

    assert await find_cached_answer(user_id=mine, question="q", ttl_hours=24) is None
    assert await find_cached_answer(user_id=theirs, question="q", ttl_hours=24) is not None


async def test_a_repeated_question_does_not_run_the_pipeline_twice(
    client: AsyncClient, monkeypatch
):
    calls = {"llm": 0}

    async def fake_retrieval(**_kwargs):
        return Retrieval(
            chunks=[
                {
                    "id": uuid4(),
                    "document_id": uuid4(),
                    "chunk_index": 0,
                    "content": "Dolo 650, twice daily",
                    "token_count": 5,
                    "document_title": "rx",
                    "document_type": "prescription",
                    "similarity": 0.9,
                    "score": 0.02,
                }
            ],
            best_similarity=0.9,
        )

    class FakeLLM:
        async def complete(self, system_instruction: str, prompt: str) -> str:
            calls["llm"] += 1
            return "Twice daily."

    monkeypatch.setattr("app.ai.answers.find_relevant_chunks", fake_retrieval)
    monkeypatch.setattr("app.ai.answers.get_llm", lambda: FakeLLM())

    await client.post(REGISTER, json={"email": EMAIL, "password": PASSWORD})
    await client.post(LOGIN, json={"email": EMAIL, "password": PASSWORD})

    first = await client.post(ASK, json={"question": "how often is dolo?"})
    second = await client.post(ASK, json={"question": "How often is Dolo?"})

    assert first.status_code == 200
    assert first.json()["cached"] is False
    assert second.status_code == 200
    assert second.json()["cached"] is True
    assert second.json()["answer"] == "Twice daily."
    assert calls["llm"] == 1


async def test_uploading_a_document_clears_cached_answers(client: AsyncClient, monkeypatch):
    cleared: list[UUID] = []

    async def spy(user_id: UUID) -> None:
        cleared.append(user_id)

    async def noop(*_args, **_kwargs) -> None:
        return None

    monkeypatch.setattr("app.controllers.documents.clear_answers_for_user", spy)
    monkeypatch.setattr("app.controllers.documents.ingest_document", noop)

    await client.post(REGISTER, json={"email": EMAIL, "password": PASSWORD})
    await client.post(LOGIN, json={"email": EMAIL, "password": PASSWORD})

    response = await client.post(
        UPLOAD,
        files={"file": ("scan.png", _png(), "image/png")},
        data={"document_type": "other"},
    )

    assert response.status_code == 201
    assert len(cleared) == 1


async def test_a_refusal_is_cached_too(client: AsyncClient, monkeypatch):
    async def fake_retrieval(**_kwargs):
        return Retrieval(chunks=[], best_similarity=0.0)

    monkeypatch.setattr("app.ai.answers.find_relevant_chunks", fake_retrieval)

    await client.post(REGISTER, json={"email": EMAIL, "password": PASSWORD})
    await client.post(LOGIN, json={"email": EMAIL, "password": PASSWORD})

    first = await client.post(ASK, json={"question": "what is my insurance number?"})
    second = await client.post(ASK, json={"question": "what is my insurance number?"})

    assert first.json()["model"] is None
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
    assert second.json()["sources"] == []
