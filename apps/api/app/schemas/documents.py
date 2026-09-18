from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class DocumentType(StrEnum):
    REPORT = "report"
    PRESCRIPTION = "prescription"
    BILL = "bill"
    SUMMARY = "summary"
    OTHER = "other"


class DocumentMetadata(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    document_type: DocumentType = DocumentType.OTHER
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None

    @field_validator("tags", mode="before")
    @classmethod
    def split_tags(cls, value: object) -> object:
        if isinstance(value, str):
            return [tag.strip().lower() for tag in value.split(",") if tag.strip()]

        return value
