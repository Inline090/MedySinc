from uuid import UUID

from app.ai.llm import get_llm
from app.ai.retrieval import find_relevant_chunks
from app.core.config import settings

REFUSAL = "No relevant information found in your documents."

QA_SYSTEM_INSTRUCTION = (
    "You answer questions using only the excerpts supplied from the patient's own "
    "medical documents. Name the source document behind each claim. If the excerpts "
    "do not contain the answer, reply with exactly this sentence and nothing else: "
    f"{REFUSAL} "
    "Never invent a medication, dosage, date, time, value or diagnosis. Never offer "
    "medical advice or a diagnosis. Keep the answer short and factual."
)


def build_context(chunks: list[dict[str, object]]) -> str:
    blocks = [
        f"[Source {position}: {chunk['document_title']}]\n{chunk['content']}"
        for position, chunk in enumerate(chunks, start=1)
    ]

    return "\n\n---\n\n".join(blocks)


def build_sources(chunks: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "document_id": chunk["document_id"],
            "document_title": chunk["document_title"],
            "document_type": chunk["document_type"],
            "chunk_index": chunk["chunk_index"],
            "similarity": round(float(chunk["similarity"]), 4),
            "excerpt": chunk["content"],
        }
        for chunk in chunks
    ]


async def answer_question(*, user_id: UUID, question: str) -> dict[str, object]:
    chunks = await find_relevant_chunks(user_id=user_id, query=question)

    best_similarity = max(
        (float(chunk["similarity"]) for chunk in chunks),
        default=0.0,
    )

    if best_similarity < settings.MIN_SIMILARITY:
        return {"answer": REFUSAL, "sources": [], "model": None}

    prompt = (
        f"Excerpts from the patient's documents:\n\n{build_context(chunks)}\n\nQuestion: {question}"
    )

    answer = await get_llm().complete(QA_SYSTEM_INSTRUCTION, prompt)

    return {
        "answer": answer or REFUSAL,
        "sources": build_sources(chunks),
        "model": settings.LLM_MODEL,
    }
