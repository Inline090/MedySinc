from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from app.ai.answers import build_context, build_sources
from app.ai.retrieval import RetrievedChunk, reciprocal_rank_fusion


def _chunk(content: str, similarity: float = 0.9) -> RetrievedChunk:
    return RetrievedChunk(
        id=uuid4(),
        document_id=uuid4(),
        chunk_index=0,
        content=content,
        token_count=10,
        document_title="Lab report",
        document_type="lab_report",
        similarity=similarity,
        score=0.02,
    )


def test_rrf_scores_a_chunk_by_one_over_k_plus_rank():
    chunk = uuid4()

    assert reciprocal_rank_fusion([[chunk]], k=60) == [(chunk, pytest.approx(1 / 61))]


def test_rrf_ranks_a_chunk_found_by_both_arms_above_one_found_by_one():
    both = uuid4()
    only_in_first = uuid4()
    only_in_second = uuid4()

    fused = reciprocal_rank_fusion([[both, only_in_first], [both, only_in_second]])
    order = [chunk_id for chunk_id, _ in fused]

    assert order[0] == both
    assert set(order[1:]) == {only_in_first, only_in_second}


def test_rrf_returns_nothing_when_both_arms_are_empty():
    assert reciprocal_rank_fusion([[], []]) == []


def test_build_context_numbers_every_source_by_title():
    context = build_context([_chunk("first excerpt"), _chunk("second excerpt")])

    assert "[Source 1: Lab report]" in context
    assert "[Source 2: Lab report]" in context
    assert "first excerpt" in context
    assert "second excerpt" in context


def test_build_sources_rounds_similarity_and_keeps_the_excerpt():
    sources = build_sources([_chunk("haemoglobin 13.5", similarity=0.812345)])

    assert sources[0]["similarity"] == 0.8123
    assert sources[0]["excerpt"] == "haemoglobin 13.5"
    assert sources[0]["document_title"] == "Lab report"


async def _seed_document(pool, *, email: str, status: str = "processed") -> tuple[UUID, UUID]:
    user_id = await pool.fetchval(
        "INSERT INTO users (email, password_hash) VALUES ($1, 'x') RETURNING id",
        email,
    )

    document_id = await pool.fetchval(
        """
        INSERT INTO documents (
            user_id, title, document_type, original_name, storage_key,
            mime_type, size_bytes, processing_status
        )
        VALUES ($1, 'Lab report', 'lab_report', 'report.pdf', 'key',
                'application/pdf', 10, $2)
        RETURNING id
        """,
        user_id,
        status,
    )

    return user_id, document_id


def _axis_vector(axis: int) -> str:
    values = ["0"] * 1024
    values[axis] = "1"

    return "[" + ",".join(values) + "]"


async def _seed_chunk(
    pool, *, user_id: UUID, document_id: UUID, index: int, content: str, axis: int
):
    await pool.execute(
        """
        INSERT INTO document_chunks (
            document_id, user_id, chunk_index, content, token_count, embedding
        )
        VALUES ($1, $2, $3, $4, $5, $6::vector)
        """,
        document_id,
        user_id,
        index,
        content,
        10,
        _axis_vector(axis),
    )


async def test_vector_search_orders_by_cosine_similarity(client: AsyncClient):
    from app.db.session import get_pool
    from app.repositories.chunks import search_chunks_by_vector

    pool = get_pool()
    user_id, document_id = await _seed_document(pool, email="vector@example.com")

    await _seed_chunk(
        pool, user_id=user_id, document_id=document_id, index=0, content="far", axis=1
    )
    await _seed_chunk(
        pool, user_id=user_id, document_id=document_id, index=1, content="near", axis=0
    )

    rows = await search_chunks_by_vector(
        user_id=user_id,
        embedding=[1.0] + [0.0] * 1023,
        limit=5,
    )

    assert [row["content"] for row in rows] == ["near", "far"]


async def test_search_never_returns_another_users_chunks(client: AsyncClient):
    from app.db.session import get_pool
    from app.repositories.chunks import search_chunks_by_text, search_chunks_by_vector

    pool = get_pool()
    mine, my_document = await _seed_document(pool, email="mine@example.com")
    theirs, their_document = await _seed_document(pool, email="theirs@example.com")

    await _seed_chunk(
        pool, user_id=mine, document_id=my_document, index=0, content="my haemoglobin", axis=0
    )
    await _seed_chunk(
        pool,
        user_id=theirs,
        document_id=their_document,
        index=0,
        content="their haemoglobin",
        axis=0,
    )

    query = [1.0] + [0.0] * 1023

    for row in await search_chunks_by_vector(user_id=mine, embedding=query, limit=10):
        assert row["content"] == "my haemoglobin"

    text_rows = await search_chunks_by_text(
        user_id=mine, embedding=query, query="haemoglobin", limit=10
    )

    assert [row["content"] for row in text_rows] == ["my haemoglobin"]


async def test_search_ignores_documents_that_are_not_processed(client: AsyncClient):
    from app.db.session import get_pool
    from app.repositories.chunks import search_chunks_by_vector

    pool = get_pool()
    user_id, ready = await _seed_document(pool, email="ready@example.com")
    pending_user, pending = await _seed_document(
        pool, email="pending@example.com", status="pending"
    )

    await _seed_chunk(pool, user_id=user_id, document_id=ready, index=0, content="ready", axis=0)
    await _seed_chunk(
        pool, user_id=pending_user, document_id=pending, index=0, content="pending", axis=0
    )

    rows = await search_chunks_by_vector(
        user_id=pending_user,
        embedding=[1.0] + [0.0] * 1023,
        limit=10,
    )

    assert rows == []


async def test_text_search_matches_on_an_exact_term(client: AsyncClient):
    from app.db.session import get_pool
    from app.repositories.chunks import search_chunks_by_text

    pool = get_pool()
    user_id, document_id = await _seed_document(pool, email="exact@example.com")

    await _seed_chunk(
        pool,
        user_id=user_id,
        document_id=document_id,
        index=0,
        content="take Dolo 650 twice",
        axis=0,
    )
    await _seed_chunk(
        pool, user_id=user_id, document_id=document_id, index=1, content="drink water", axis=1
    )

    rows = await search_chunks_by_text(
        user_id=user_id,
        embedding=[1.0] + [0.0] * 1023,
        query="Dolo",
        limit=10,
    )

    assert [row["content"] for row in rows] == ["take Dolo 650 twice"]
