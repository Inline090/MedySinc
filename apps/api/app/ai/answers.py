import json
from uuid import UUID

from app.ai.llm import get_llm
from app.ai.retrieval import RetrievedChunk, find_relevant_chunks
from app.core.config import settings
from app.repositories.answers import find_cached_answer, save_answer

REFUSAL = "No relevant information found in your documents."

QA_SYSTEM_INSTRUCTION = (
    "You answer questions using only the excerpts supplied from the patient's own "
    "medical documents. Name the source document behind each claim. If the excerpts "
    "do not contain the answer, reply with exactly this sentence and nothing else: "
    f"{REFUSAL} "
    "Never invent a medication, dosage, date, time, value or diagnosis. Never offer "
    "medical advice or a diagnosis. Keep the answer short and factual."
)


def build_context(chunks: list[RetrievedChunk]) -> str:
    blocks = [
        f"[Source {position}: {chunk['document_title']}]\n{chunk['content']}"
        for position, chunk in enumerate(chunks, start=1)
    ]

    return "\n\n---\n\n".join(blocks)


def build_sources(chunks: list[RetrievedChunk]) -> list[dict[str, object]]:
    # JSON-native types only: these are serialised into the response and stored in the
    # answer cache, and a raw UUID is not JSON serialisable.
    return [
        {
            "document_id": str(chunk["document_id"]),
            "document_title": chunk["document_title"],
            "document_type": chunk["document_type"],
            "chunk_index": chunk["chunk_index"],
            "similarity": round(float(chunk["similarity"]), 4),
            "excerpt": chunk["content"],
        }
        for chunk in chunks
    ]


async def _cached(user_id: UUID, question: str) -> dict[str, object] | None:
    if not settings.ANSWER_CACHE_ENABLED:
        return None

    row = await find_cached_answer(
        user_id=user_id,
        question=question,
        ttl_hours=settings.ANSWER_CACHE_TTL_HOURS,
    )

    if row is None:
        return None

    return {
        "answer": row["answer"],
        "sources": json.loads(row["sources"]),
        "model": row["model"],
        "cached": True,
    }


async def answer_question(*, user_id: UUID, question: str) -> dict[str, object]:
    hit = await _cached(user_id, question)

    if hit is not None:
        return hit

    retrieval = await find_relevant_chunks(user_id=user_id, query=question)

    if retrieval.best_similarity < settings.MIN_SIMILARITY:
        result: dict[str, object] = {"answer": REFUSAL, "sources": [], "model": None}
    else:
        prompt = (
            f"Excerpts from the patient's documents:\n\n{build_context(retrieval.chunks)}\n\n"
            f"Question: {question}"
        )

        answer = await get_llm().complete(QA_SYSTEM_INSTRUCTION, prompt)

        result = {
            "answer": answer or REFUSAL,
            "sources": build_sources(retrieval.chunks),
            "model": settings.LLM_MODEL,
        }

    if settings.ANSWER_CACHE_ENABLED:
        await save_answer(
            user_id=user_id,
            question=question,
            answer=str(result["answer"]),
            sources=result["sources"],  # type: ignore[arg-type]
            model=result["model"],  # type: ignore[arg-type]
        )

    return {**result, "cached": False}
