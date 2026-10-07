"""The documents feature: upload, list, read, delete, and summarize documents."""

import hashlib
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

import asyncpg
import filetype
from asyncpg.exceptions import UniqueViolationError
from fastapi import BackgroundTasks, Depends, File, Form, Query, Response, UploadFile

from app.ai.ingestion import ingest_document
from app.ai.summaries import generate_document_summary
from app.core.config import settings
from app.core.exceptions import AppError
from app.middlewares.auth import get_current_user
from app.repositories.answers import clear_answers_for_user
from app.repositories.documents import (
    count_documents,
    create_document,
    delete_document,
    find_document_by_content_hash,
    find_document_for_user,
    list_documents,
    update_document_metadata,
)
from app.schemas.documents import DocumentUpdate
from app.storage import get_storage

ALLOWED_MIME_TYPES = {"application/pdf", "image/png", "image/jpeg"}


def document_summary(document: asyncpg.Record) -> dict[str, object]:
    """Formats a document row to return in a list."""

    return {
        "id": document["id"],
        "title": document["title"],
        "notes": document["notes"],
        "original_name": document["original_name"],
        "mime_type": document["mime_type"],
        "size_bytes": document["size_bytes"],
        "processing_status": document["processing_status"],
        "created_at": document["created_at"],
        "updated_at": document["updated_at"],
    }


def document_detail(document: asyncpg.Record) -> dict[str, object]:
    """Formats a document row to return its full details."""

    return {
        **document_summary(document),
        "extracted_text": document["extracted_text"],
        "summary": document["summary"],
        "summary_model": document["summary_model"],
    }


async def upload_document(
    background: BackgroundTasks,
    user: Annotated[asyncpg.Record, Depends(get_current_user)],
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form()] = None,
    notes: Annotated[str | None, Form()] = None,
) -> dict[str, object]:
    """Receives an uploaded file, saves it, and starts processing it in the background."""

    limit_mb = settings.MAX_UPLOAD_BYTES // (1024 * 1024)

    if file.size is not None and file.size > settings.MAX_UPLOAD_BYTES:
        raise AppError(f"File is larger than the {limit_mb} MB limit", 413)

    data = await file.read()

    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise AppError(f"File is larger than the {limit_mb} MB limit", 413)

    detected = filetype.guess(data)

    if detected is None or detected.mime not in ALLOWED_MIME_TYPES:
        raise AppError("Unsupported file type - expected PDF, PNG or JPEG", 415)

    original_name = (file.filename or "document")[:255]
    content_hash = hashlib.sha256(data).hexdigest()

    if await find_document_by_content_hash(user["id"], content_hash) is not None:
        raise AppError("You have already uploaded this file", 409)

    storage_key = f"originals/{user['id']}/{uuid4()}"

    await get_storage().save(storage_key, data, detected.mime)

    try:
        document = await create_document(
            user_id=user["id"],
            title=(title or Path(original_name).stem or "document")[:255],
            original_name=original_name,
            storage_key=storage_key,
            mime_type=detected.mime,
            size_bytes=len(data),
            content_hash=content_hash,
            notes=notes,
        )
    except UniqueViolationError as error:
        # Two uploads of the same bytes raced past the check above.
        raise AppError("You have already uploaded this file", 409) from error

    background.add_task(ingest_document, document["id"])
    await clear_answers_for_user(user["id"])

    return {"document": document_detail(document)}


async def list_user_documents(
    user: Annotated[asyncpg.Record, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, object]:
    """Lists the logged-in user's documents, starting with the newest."""

    documents = await list_documents(
        user_id=user["id"],
        limit=limit,
        offset=offset,
    )

    total = await count_documents(user_id=user["id"])

    return {
        "documents": [document_summary(item) for item in documents],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


async def get_user_document(
    user: Annotated[asyncpg.Record, Depends(get_current_user)],
    document_id: UUID,
) -> dict[str, object]:
    """Gets a single document, including its text and summary."""

    document = await find_document_for_user(document_id, user["id"])

    if document is None:
        raise AppError("Document not found", 404)

    return {"document": document_detail(document)}


async def delete_user_document(
    user: Annotated[asyncpg.Record, Depends(get_current_user)],
    document_id: UUID,
) -> dict[str, str]:
    """Deletes a document, its file, and clears cached answers."""

    storage_key = await delete_document(document_id, user["id"])

    if storage_key is None:
        raise AppError("Document not found", 404)

    await get_storage().delete(storage_key)
    await clear_answers_for_user(user["id"])

    return {"message": "Document deleted"}


async def summarize_user_document(
    user: Annotated[asyncpg.Record, Depends(get_current_user)],
    document_id: UUID,
) -> dict[str, object]:
    """Creates and saves a summary for a document."""

    document = await find_document_for_user(document_id, user["id"])

    if document is None:
        raise AppError("Document not found", 404)

    summary = await generate_document_summary(document_id)

    return {"summary": summary, "model": settings.LLM_MODEL}


async def download_user_document(
    user: Annotated[asyncpg.Record, Depends(get_current_user)],
    document_id: UUID,
) -> Response:
    """Downloads the original file the user uploaded."""

    document = await find_document_for_user(document_id, user["id"])

    if document is None:
        raise AppError("Document not found", 404)

    data = await get_storage().read(document["storage_key"])

    name = "".join(c for c in document["original_name"] if c.isalnum() or c in " ._-").strip()
    filename = name or "document"

    return Response(
        content=data,
        media_type=document["mime_type"],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def update_user_document(
    user: Annotated[asyncpg.Record, Depends(get_current_user)],
    document_id: UUID,
    payload: DocumentUpdate,
) -> dict[str, object]:
    """Updates a document's title or notes."""

    document = await update_document_metadata(
        document_id,
        user["id"],
        title=payload.title,
        notes=payload.notes,
    )

    if document is None:
        raise AppError("Document not found", 404)

    return {"document": document_detail(document)}
