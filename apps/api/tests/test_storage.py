import pytest

from app.core.config import settings
from app.core.exceptions import AppError
from app.storage import get_storage
from app.storage.local import LocalStorage
from app.storage.s3 import S3Storage


@pytest.fixture(autouse=True)
def clear_storage_cache():
    """Clears the get_storage() cache before and after each test."""
    get_storage.cache_clear()
    yield
    get_storage.cache_clear()


async def test_local_storage_round_trip(tmp_path, monkeypatch):
    """Checks that saving, reading, and deleting files works locally."""
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "local")
    monkeypatch.setattr(settings, "STORAGE_ROOT", str(tmp_path))

    storage = get_storage()

    assert isinstance(storage, LocalStorage)

    await storage.save("originals/user-1/file", b"hello", "application/pdf")

    assert await storage.read("originals/user-1/file") == b"hello"

    await storage.delete("originals/user-1/file")

    with pytest.raises(FileNotFoundError):
        await storage.read("originals/user-1/file")


async def test_local_storage_refuses_a_key_that_escapes_the_root(tmp_path):
    """Checks that file paths can't go outside the storage directory."""
    storage = LocalStorage(tmp_path)

    with pytest.raises(ValueError):
        await storage.save("../escaped", b"hello", "application/pdf")


async def test_storage_selects_s3_when_configured(monkeypatch):
    """Checks that S3 is used when the settings tell it to."""
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "s3")
    monkeypatch.setattr(settings, "S3_BUCKET", "medsync-test")
    monkeypatch.setattr(settings, "S3_REGION", "ap-south-1")
    monkeypatch.setattr(settings, "S3_ENDPOINT", "http://localhost:9000")

    assert isinstance(get_storage(), S3Storage)


async def test_s3_backend_requires_a_bucket(monkeypatch):
    """Checks that S3 setup fails if no bucket name is given."""
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "s3")
    monkeypatch.setattr(settings, "S3_BUCKET", None)

    with pytest.raises(AppError):
        get_storage()
