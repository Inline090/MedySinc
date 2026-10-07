from uuid import uuid4

from httpx import AsyncClient

from app.ai.retrieval import Retrieval

ASK = "/api/v1/ask"
REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"

EMAIL = "states@example.com"
PASSWORD = "secret123"


def _chunk(similarity: float) -> dict[str, object]:
    """Creates a fake document chunk with the given similarity score."""
    return {
        "id": uuid4(),
        "document_id": uuid4(),
        "chunk_index": 0,
        "content": "Dolo 650, twice daily",
        "token_count": 5,
        "document_title": "rx",
        "similarity": similarity,
        "score": 0.02,
    }


async def _sign_in(client: AsyncClient) -> None:
    """Registers and logs in a test user."""
    await client.post(REGISTER, json={"email": EMAIL, "password": PASSWORD})
    await client.post(LOGIN, json={"email": EMAIL, "password": PASSWORD})


class _CountingLLM:
    def __init__(self) -> None:
        """Sets up the fake LLM to count how many times it's called."""
        self.calls = 0

    async def complete(self, system_instruction: str, prompt: str) -> str:
        """Counts the call and returns a fixed answer."""
        self.calls += 1
        return "Twice daily."


async def test_a_weak_match_is_answered_with_low_confidence(client: AsyncClient, monkeypatch):
    """Answers with 'Low' confidence if the match is weak."""

    async def weak_retrieval(**_kwargs):
        return Retrieval(chunks=[_chunk(0.5)], best_similarity=0.5)

    llm = _CountingLLM()

    monkeypatch.setattr("app.ai.answers.find_relevant_chunks", weak_retrieval)
    monkeypatch.setattr("app.ai.answers.get_llm", lambda: llm)

    await _sign_in(client)

    response = await client.post(ASK, json={"question": "how often is dolo?"})
    body = response.json()

    assert body["status"] == "uncertain"
    assert body["confidence"] == "Low"
    assert body["model"] is not None
    assert body["answer"] == "Twice daily."
    assert len(body["sources"]) == 1
    assert llm.calls == 1


async def test_a_confident_match_is_answered_with_high_confidence(client: AsyncClient, monkeypatch):
    """Answers with 'High' confidence if the match is strong."""

    async def strong_retrieval(**_kwargs):
        return Retrieval(chunks=[_chunk(0.9)], best_similarity=0.9)

    llm = _CountingLLM()

    monkeypatch.setattr("app.ai.answers.find_relevant_chunks", strong_retrieval)
    monkeypatch.setattr("app.ai.answers.get_llm", lambda: llm)

    await _sign_in(client)

    response = await client.post(ASK, json={"question": "how often is dolo?"})
    body = response.json()

    assert body["status"] == "answered"
    assert body["confidence"] == "High"
    assert body["model"] is not None
    assert llm.calls == 1


async def test_nothing_relevant_is_refused_without_calling_the_model(
    client: AsyncClient, monkeypatch
):
    """Returns 'not found' without calling the model if there are no good matches."""

    async def empty_retrieval(**_kwargs):
        return Retrieval(chunks=[_chunk(0.2)], best_similarity=0.2)

    llm = _CountingLLM()

    monkeypatch.setattr("app.ai.answers.find_relevant_chunks", empty_retrieval)
    monkeypatch.setattr("app.ai.answers.get_llm", lambda: llm)

    await _sign_in(client)

    response = await client.post(ASK, json={"question": "what is my blood type?"})
    body = response.json()

    assert body["status"] == "not_found"
    assert body["confidence"] is None
    assert body["sources"] == []
    assert body["model"] is None
    assert llm.calls == 0


async def test_the_uncertain_state_survives_a_cache_round_trip(client: AsyncClient, monkeypatch):
    """Checks that a cached 'Low' confidence answer keeps its label."""

    async def weak_retrieval(**_kwargs):
        return Retrieval(chunks=[_chunk(0.5)], best_similarity=0.5)

    monkeypatch.setattr("app.ai.answers.find_relevant_chunks", weak_retrieval)

    await _sign_in(client)

    await client.post(ASK, json={"question": "borderline question"})
    second = await client.post(ASK, json={"question": "borderline question"})

    assert second.json()["cached"] is True
    assert second.json()["status"] == "uncertain"
    assert second.json()["confidence"] == "Low"
