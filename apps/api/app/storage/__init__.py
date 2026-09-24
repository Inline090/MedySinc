from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import AppError
from app.storage.base import Storage
from app.storage.local import LocalStorage
from app.storage.s3 import S3Storage


@lru_cache
def get_storage() -> Storage:
    if settings.STORAGE_BACKEND == "s3":
        if not settings.S3_BUCKET:
            raise AppError("S3_BUCKET must be set when STORAGE_BACKEND is s3", 503)

        return S3Storage(
            bucket=settings.S3_BUCKET,
            region=settings.S3_REGION,
            endpoint_url=settings.S3_ENDPOINT or None,
        )

    return LocalStorage(Path(settings.STORAGE_ROOT))
