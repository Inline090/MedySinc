"""Answers a question using a user's documents."""

import json
from uuid import UUID

from app.ai.llm import get_llm
from app.ai.redaction import redact
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
    """Turns search results into text for the AI prompt."""

    blocks = [
        f"[Source {position}: {chunk['document_title']}]\n{chunk['content']}"
        for position, chunk in enumerate(chunks, start=1)
    ]

    return "\n\n---\n\n".join(blocks)


def build_sources(chunks: list[RetrievedChunk]) -> list[dict[str, object]]:
    """Turns search results into citations for the user."""

    # Only use standard JSON types because this goes to the user and the database.
    return [
        {
            "document_id": str(chunk["document_id"]),
            "document_title": chunk["document_title"],
            "chunk_index": chunk["chunk_index"],
            "similarity": round(float(chunk["similarity"]), 4),
            "excerpt": chunk["content"],
        }
        for chunk in chunks
    ]


async def _cached(user_id: UUID, question: str) -> dict[str, object] | None:
    """Checks if we already answered this exact question."""

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
        "status": row["status"],
        "answer": row["answer"],
        "sources": json.loads(row["sources"]),
        "model": row["model"],
        "confidence": _confidence_for(str(row["status"])),
        "cached": True,
    }


def _confidence_for(status: str) -> str | None:
    """Turns a status string into a confidence label."""

    if status == "answered":
        return "High"

    if status == "uncertain":
        return "Low"

    return None


async def answer_question(*, user_id: UUID, question: str) -> dict[str, object]:
    """Answers a question using a user's documents."""

    hit = await _cached(user_id, question)

    if hit is not None:
        return hit

    retrieval = await find_relevant_chunks(user_id=user_id, query=question)

    if retrieval.best_similarity < settings.MIN_SIMILARITY:
        # No relevant documents found, so we can't answer. We return a refusal.
        result: dict[str, object] = {
            "status": "not_found",
            "answer": REFUSAL,
            "sources": [],
            "model": None,
            "confidence": None,
        }
    else:
        # Both strong and weak matches get an AI answer. The score just decides the label.
        confident = retrieval.best_similarity >= settings.CONFIDENT_SIMILARITY

        prompt = (
            f"Excerpts from the patient's documents:\n\n"
            f"{redact(build_context(retrieval.chunks))}\n\n"
            f"Question: {question}"
        )

        answer = await get_llm().complete(QA_SYSTEM_INSTRUCTION, prompt)

        result = {
            "status": "answered" if confident else "uncertain",
            "answer": answer or REFUSAL,
            "sources": build_sources(retrieval.chunks),
            "model": settings.LLM_MODEL,
            "confidence": "High" if confident else "Low",
        }

    if settings.ANSWER_CACHE_ENABLED:
        await save_answer(
            user_id=user_id,
            question=question,
            answer=str(result["answer"]),
            sources=result["sources"],  # type: ignore[arg-type]
            model=result["model"],  # type: ignore[arg-type]
            status=str(result["status"]),
        )

    return {**result, "cached": False}
