"""Request shapes for the documents endpoints."""

from pydantic import BaseModel, Field


class DocumentUpdate(BaseModel):
    """Body of PATCH /api/v1/documents/{document_id}."""

    title: str | None = Field(default=None, max_length=255)
    notes: str | None = None
