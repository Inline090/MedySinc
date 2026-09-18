from pathlib import Path
from typing import Annotated
from uuid import uuid4

import asyncpg
import filetype
from fastapi import Depends, File, Form, UploadFile

from app.core.config import settings
from app.core.exceptions import AppError
from app.middlewares.auth import get_current_user
from app.repositories.documents import create_document
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
    return {**document_summary(document), "extracted_text": document["extracted_text"]}


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
    user: Annotated[asyncpg.Record, Depends(get_current_user)],
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form()] = None,
    document_type: Annotated[DocumentType, Form()] = DocumentType.OTHER,
    tags: Annotated[str | None, Form()] = None,
    notes: Annotated[str | None, Form()] = None,
) -> dict[str, object]:
    data = await file.read()
    limit_mb = settings.MAX_UPLOAD_BYTES // (1024 * 1024)

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

    return {"document": document_detail(document)}
