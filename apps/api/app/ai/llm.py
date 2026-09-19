from functools import lru_cache
from typing import Protocol

from google import genai

from app.core.config import settings
from app.core.exceptions import AppError


class LLMProvider(Protocol):
    async def complete(self, system_instruction: str, prompt: str) -> str: ...


class GeminiProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def complete(self, system_instruction: str, prompt: str) -> str:
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0,
            ),
        )

        return (response.text or "").strip()


@lru_cache
def get_llm() -> LLMProvider:
    if not settings.AI_API_KEY:
        raise AppError("No AI provider key is configured", 503)

    return GeminiProvider(settings.AI_API_KEY, settings.LLM_MODEL)
