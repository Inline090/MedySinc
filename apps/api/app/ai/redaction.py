"""Removing personal contact details before text is sent to the model."""

import re

PLACEHOLDER = "[redacted]"

_PHONE = re.compile(r"\+?\d(?:[\s.\-()]?\d){9,}")

_EMAIL = re.compile(r"[\w.+\-]+@[\w\-]+\.[\w.\-]+")


def redact(text: str) -> str:
    """Replaces personal contact details in text with a placeholder."""

    if not text:
        return text

    return _EMAIL.sub(PLACEHOLDER, _PHONE.sub(PLACEHOLDER, text))
