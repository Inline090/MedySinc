from uuid import UUID

from app.ai.llm import get_llm
from app.core.config import settings
from app.core.exceptions import AppError
from app.repositories.documents import find_document_by_id, update_document_summary

SUMMARY_SYSTEM_INSTRUCTION = (
    "You summarise a single medical document for the patient who uploaded it. "
    "Use only the text you are given. Never add facts, values, dates, medications "
    "or diagnoses that are not present in it, and never infer a detail that is "
    "missing - leave it out instead. Write short, plain, factual prose."
)


async def generate_document_summary(document_id: UUID) -> str:
    document = await find_document_by_id(document_id)

    if document is None:
        raise AppError("Document not found", 404)

    text = (document["extracted_text"] or "").strip()

    if not text:
        raise AppError("This document has no extracted text to summarise", 409)

    summary = await get_llm().complete(SUMMARY_SYSTEM_INSTRUCTION, text)

    if not summary:
        raise AppError("The summarisation model returned nothing", 502)

    await update_document_summary(document_id, summary=summary, model=settings.LLM_MODEL)

    return summary
