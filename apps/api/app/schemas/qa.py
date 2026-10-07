"""Request shape for the question-answering endpoint."""

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """Body of POST /api/v1/ask."""

    question: str = Field(min_length=3, max_length=500)
