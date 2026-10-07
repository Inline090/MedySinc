"""Processes an uploaded file so it can be searched later."""

from contextlib import suppress
from uuid import UUID

import anyio

from app.ai.chunking import chunk_text
from app.ai.embeddings import get_embeddings
from app.ai.extraction import extract_text
from app.ai.medicines import extract_medicines
from app.core.exceptions import AppError
from app.repositories.chunks import replace_document_chunks
from app.repositories.documents import find_document_by_id, update_document_processing
from app.repositories.medicines import replace_document_medicines
from app.storage import get_storage


async def ingest_document(document_id: UUID) -> int:
    """Takes one uploaded document and makes it searchable."""

    document = await find_document_by_id(document_id)

    if document is None:
        raise AppError("Document not found", 404)

    await update_document_processing(document_id, status="processing")

    try:
        data = await get_storage().read(document["storage_key"])
        text = await anyio.to_thread.run_sync(extract_text, data, document["mime_type"])

        chunks = chunk_text(text)

        if not chunks:
            raise AppError("No text could be extracted from this document", 422)

        vectors = await get_embeddings().embed([chunk.content for chunk in chunks])

        await replace_document_chunks(
            document_id=document_id,
            user_id=document["user_id"],
            chunks=[
                (chunk.index, chunk.content, chunk.token_count, vector)
                for chunk, vector in zip(chunks, vectors, strict=True)
            ],
        )
    except Exception as error:
        await update_document_processing(document_id, status="failed", error=str(error))
        raise

    with suppress(Exception):
        await replace_document_medicines(
            document_id=document_id,
            user_id=document["user_id"],
            rows=await extract_medicines(text),
        )

    await update_document_processing(document_id, status="processed", extracted_text=text)

    return len(chunks)
