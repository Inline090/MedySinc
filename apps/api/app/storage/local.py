"""Storage on the local filesystem for development."""

from pathlib import Path

import anyio

from app.storage.base import Storage


class LocalStorage(Storage):
    """Stores documents as files under one root directory."""

    def __init__(self, root: Path) -> None:
        """Record the root, resolved to an absolute path."""

        self._root = root.resolve()

    def _resolve(self, key: str) -> Path:
        """Turn a storage key into an absolute path inside the root, or refuse."""

        candidate = (self._root / key).resolve()

        if not candidate.is_relative_to(self._root):
            raise ValueError(f"Storage key escapes the storage root: {key}")

        return candidate

    async def save(self, key: str, data: bytes, content_type: str) -> None:
        """Write bytes to disk under the given key."""

        await anyio.to_thread.run_sync(self._write, self._resolve(key), data)

    async def read(self, key: str) -> bytes:
        """Read the bytes stored under the given key."""

        return await anyio.to_thread.run_sync(self._resolve(key).read_bytes)

    async def delete(self, key: str) -> None:
        """Remove the file stored under the given key."""

        await anyio.to_thread.run_sync(self._unlink, self._resolve(key))

    @staticmethod
    def _write(path: Path, data: bytes) -> None:
        """Create the parent directories and write the file. Blocking."""

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    @staticmethod
    def _unlink(path: Path) -> None:
        """Delete a file, tolerating its absence. Blocking."""

        path.unlink(missing_ok=True)
