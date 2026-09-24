from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

import asyncpg
import filetype
from fastapi import BackgroundTasks, Depends, File, Form, Query, UploadFile

from app.ai.ingestion import ingest_document
from app.ai.summaries import generate_document_summary
from app.core.config import settings
from app.core.exceptions import AppError
from app.middlewares.auth import get_current_user
from app.repositories.documents import (
    count_documents,
    create_document,
    delete_document,
    find_document_for_user,
    list_documents,
)
from app.schemas.documents import DocumentType
from app.storage import get_storage

ALLOWED_MIME_TYPES = {"application/pdf", "image/png", "image/jpeg"}


def document_summary(document: asyncpg.Record) -> dict[str, object]:
    return {
        "id": document["id"],
        "title": document["title"],
        "document_type": document["document_type"],
        "tags": list(document["tags"]),
        "notes": document["notes"],
        "original_name": document["original_name"],
        "mime_type": document["mime_type"],
        "size_bytes": document["size_bytes"],
        "processing_status": document["processing_status"],
        "created_at": document["created_at"],
        "updated_at": document["updated_at"],
    }


def document_detail(document: asyncpg.Record) -> dict[str, object]:
    return {
        **document_summary(document),
        "extracted_text": document["extracted_text"],
        "summary": document["summary"],
        "summary_model": document["summary_model"],
    }


def parse_tags(raw: str | None) -> list[str]:
    if raw is None:
        return []

    ordered: dict[str, None] = {}

    for tag in raw.split(","):
        cleaned = tag.strip().lower()

        if cleaned:
            ordered.setdefault(cleaned, None)

    return list(ordered)


async def upload_document(
    background: BackgroundTasks,
    user: Annotated[asyncpg.Record, Depends(get_current_user)],
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form()] = None,
    document_type: Annotated[DocumentType, Form()] = DocumentType.OTHER,
    tags: Annotated[str | None, Form()] = None,
    notes: Annotated[str | None, Form()] = None,
) -> dict[str, object]:
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
    storage_key = f"originals/{user['id']}/{uuid4()}"

    await get_storage().save(storage_key, data, detected.mime)

    document = await create_document(
        user_id=user["id"],
        title=(title or Path(original_name).stem or "document")[:255],
        document_type=document_type.value,
        original_name=original_name,
        storage_key=storage_key,
        mime_type=detected.mime,
        size_bytes=len(data),
        tags=parse_tags(tags),
        notes=notes,
    )

    background.add_task(ingest_document, document["id"])

    return {"document": document_detail(document)}


async def list_user_documents(
    user: Annotated[asyncpg.Record, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    document_type: Annotated[DocumentType | None, Query()] = None,
    tag: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query(min_length=2, max_length=100)] = None,
) -> dict[str, object]:
    type_filter = document_type.value if document_type is not None else None
    tag_filter = tag.strip().lower() if tag is not None else None
    search_filter = search.strip() if search is not None else None

    documents = await list_documents(
        user_id=user["id"],
        limit=limit,
        offset=offset,
        document_type=type_filter,
        tag=tag_filter,
        search=search_filter,
    )

    total = await count_documents(
        user_id=user["id"],
        document_type=type_filter,
        tag=tag_filter,
        search=search_filter,
    )

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
    document = await find_document_for_user(document_id, user["id"])

    if document is None:
        raise AppError("Document not found", 404)

    return {"document": document_detail(document)}


async def delete_user_document(
    user: Annotated[asyncpg.Record, Depends(get_current_user)],
    document_id: UUID,
) -> dict[str, str]:
    storage_key = await delete_document(document_id, user["id"])

    if storage_key is None:
        raise AppError("Document not found", 404)

    await get_storage().delete(storage_key)

    return {"message": "Document deleted"}


async def summarize_user_document(
    user: Annotated[asyncpg.Record, Depends(get_current_user)],
    document_id: UUID,
) -> dict[str, object]:
    document = await find_document_for_user(document_id, user["id"])

    if document is None:
        raise AppError("Document not found", 404)

    summary = await generate_document_summary(document_id)

    return {"summary": summary, "model": settings.LLM_MODEL}
