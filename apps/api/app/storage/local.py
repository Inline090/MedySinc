from pathlib import Path

import anyio

from app.storage.base import Storage


class LocalStorage(Storage):
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def _resolve(self, key: str) -> Path:
        candidate = (self._root / key).resolve()

        if not candidate.is_relative_to(self._root):
            raise ValueError(f"Storage key escapes the storage root: {key}")

        return candidate

    async def save(self, key: str, data: bytes, content_type: str) -> None:
        await anyio.to_thread.run_sync(self._write, self._resolve(key), data)

    async def read(self, key: str) -> bytes:
        return await anyio.to_thread.run_sync(self._resolve(key).read_bytes)

    async def delete(self, key: str) -> None:
        await anyio.to_thread.run_sync(self._unlink, self._resolve(key))

    @staticmethod
    def _write(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    @staticmethod
    def _unlink(path: Path) -> None:
        path.unlink(missing_ok=True)
