import re
from dataclasses import dataclass

CHARS_PER_TOKEN = 4
MAX_TOKENS = 512
OVERLAP_TOKENS = 64

MAX_CHARS = MAX_TOKENS * CHARS_PER_TOKEN
OVERLAP_CHARS = OVERLAP_TOKENS * CHARS_PER_TOKEN

_WHITESPACE = re.compile(r"\s+")
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class Chunk:
    index: int
    content: str
    token_count: int


def estimate_tokens(text: str) -> int:
    return max(1, round(len(text) / CHARS_PER_TOKEN))


def split_sentences(text: str) -> list[str]:
    normalized = _WHITESPACE.sub(" ", text).strip()

    if not normalized:
        return []

    return [part.strip() for part in _SENTENCE_BOUNDARY.split(normalized) if part.strip()]


def _split_oversized(unit: str, max_chars: int) -> list[str]:
    if len(unit) <= max_chars:
        return [unit]

    pieces: list[str] = []
    current: list[str] = []
    length = 0

    for word in unit.split(" "):
        if current and length + len(word) + 1 > max_chars:
            pieces.append(" ".join(current))
            current = []
            length = 0

        current.append(word)
        length += len(word) + 1

    if current:
        pieces.append(" ".join(current))

    return pieces


def _overlap_units(units: list[str], overlap_chars: int) -> list[str]:
    if overlap_chars <= 0:
        return []

    tail: list[str] = []
    length = 0

    for unit in reversed(units):
        if length + len(unit) + 1 > overlap_chars:
            break

        tail.insert(0, unit)
        length += len(unit) + 1

    return tail


def chunk_text(
    text: str,
    max_tokens: int = MAX_TOKENS,
    overlap_tokens: int = OVERLAP_TOKENS,
) -> list[Chunk]:
    max_chars = max_tokens * CHARS_PER_TOKEN
    overlap_chars = overlap_tokens * CHARS_PER_TOKEN

    units: list[str] = []

    for sentence in split_sentences(text):
        units.extend(_split_oversized(sentence, max_chars))

    if not units:
        return []

    chunks: list[Chunk] = []
    current: list[str] = []
    current_length = 0

    for unit in units:
        if current and current_length + len(unit) + 1 > max_chars:
            content = " ".join(current).strip()
            chunks.append(Chunk(len(chunks), content, estimate_tokens(content)))

            carried = _overlap_units(current, overlap_chars)
            carried_length = sum(len(item) + 1 for item in carried)

            while carried and carried_length + len(unit) + 1 > max_chars:
                carried_length -= len(carried.pop(0)) + 1

            current = carried
            current_length = carried_length

        current.append(unit)
        current_length += len(unit) + 1

    if current:
        content = " ".join(current).strip()

        if content:
            chunks.append(Chunk(len(chunks), content, estimate_tokens(content)))

    return chunks
