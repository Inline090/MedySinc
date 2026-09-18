from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from app.storage.base import Storage
from app.storage.local import LocalStorage


@lru_cache
def get_storage() -> Storage:
    return LocalStorage(Path(settings.STORAGE_ROOT))
