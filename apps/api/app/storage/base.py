"""The storage interface."""

from typing import Protocol


class Storage(Protocol):
    """Where uploaded documents are stored."""

    async def save(self, key: str, data: bytes, content_type: str) -> None:
        """Stores file bytes under a specific key."""
        ...

    async def read(self, key: str) -> bytes:
        """Retrieves the file bytes for a given key."""
        ...

    async def delete(self, key: str) -> None:
        """Deletes the file stored at a given key."""
        ...
