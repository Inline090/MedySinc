"""Connects to an AI language model (like Gemini)."""

from functools import lru_cache
from typing import Protocol

import anyio
from google import genai

from app.core.config import settings
from app.core.exceptions import AppError


class LLMProvider(Protocol):
    """The required structure for any AI model class."""

    async def complete(self, system_instruction: str, prompt: str) -> str: ...


class GeminiProvider:
    """Uses the Gemini AI to generate text."""

    def __init__(self, api_key: str, model: str) -> None:
        """Sets up the connection to Gemini."""

        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def complete(self, system_instruction: str, prompt: str) -> str:
        """Sends a prompt to the AI and gets its answer."""

        try:
            with anyio.fail_after(settings.LLM_TIMEOUT_SECONDS):
                response = await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0,
                    ),
                )
        except TimeoutError as error:
            raise AppError(
                f"The language model did not respond within {settings.LLM_TIMEOUT_SECONDS} seconds",
                504,
            ) from error

        return (response.text or "").strip()


@lru_cache
def get_llm() -> LLMProvider:
    """Gets the AI connection tool, creating it if needed."""

    if not settings.AI_API_KEY:
        raise AppError("No AI provider key is configured", 503)

    return GeminiProvider(settings.AI_API_KEY, settings.LLM_MODEL)
