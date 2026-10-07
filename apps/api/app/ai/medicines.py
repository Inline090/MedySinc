"""Finds and verifies medicine details in a document."""

import json
from typing import Any

from app.ai.llm import get_llm
from app.ai.redaction import redact

MEDICINE_SYSTEM_INSTRUCTION = (
    "You read a single medical prescription and list the medicines in it. "
    "Reply with a JSON array and nothing else. Each element must be an object with "
    "exactly these keys: medicine, dose, frequency, prescribed_on, hospital, notes. "
    "Use null for any field the document does not state. Never guess a value, and "
    "never fill a field to make the object look complete. "
    "Copy each value EXACTLY as it appears in the document - do not correct spelling, "
    "expand abbreviations, or reformat a date. If the document lists no medicines, "
    "reply with []."
)

FIELDS = ("hospital", "medicine", "dose", "frequency", "prescribed_on", "notes")


def _parse(raw: str) -> list[dict[str, Any]]:
    """Turns the AI's response into a JSON list. Handles markdown formatting."""

    text = raw.strip()

    if text.startswith("```"):
        text = text.split("```")[1].removeprefix("json").strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return []

    if not isinstance(parsed, list):
        return []

    return [item for item in parsed if isinstance(item, dict)]


def verify(rows: list[dict[str, Any]], source: str) -> list[dict[str, Any]]:
    """Removes any details that aren't actually in the document."""

    haystack = source.lower()
    kept: list[dict[str, Any]] = []

    for row in rows:
        cleaned: dict[str, Any] = {}

        for field in FIELDS:
            value = row.get(field)
            text = str(value).strip() if value is not None else ""

            cleaned[field] = text if text and text.lower() in haystack else None

        if cleaned["medicine"] is None:
            continue

        kept.append(cleaned)

    return kept


async def extract_medicines(text: str) -> list[dict[str, Any]]:
    """Finds and verifies medicines in a document's full text."""

    if not text.strip():
        return []

    try:
        # The whole document is sent, so the contact details are stripped first.
        raw = await get_llm().complete(MEDICINE_SYSTEM_INSTRUCTION, redact(text))
    except Exception:
        return []

    return verify(_parse(raw), text)
