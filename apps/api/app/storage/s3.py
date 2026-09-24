from typing import Any

import anyio
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.exceptions import AppError
from app.storage.base import Storage


class S3Storage(Storage):
    def __init__(self, bucket: str, region: str, endpoint_url: str | None = None) -> None:
        self._bucket = bucket
        self._region = region
        self._endpoint_url = endpoint_url
        self._client = None

    def _connection(self) -> Any:
        if self._client is None:
            self._client = boto3.client(
                "s3",
                region_name=self._region,
                endpoint_url=self._endpoint_url,
                config=Config(s3={"addressing_style": "path"}) if self._endpoint_url else None,
            )

        return self._client

    async def save(self, key: str, data: bytes, content_type: str) -> None:
        await anyio.to_thread.run_sync(self._put, key, data, content_type)

    async def read(self, key: str) -> bytes:
        return await anyio.to_thread.run_sync(self._get, key)

    async def delete(self, key: str) -> None:
        await anyio.to_thread.run_sync(self._delete, key)

    def _put(self, key: str, data: bytes, content_type: str) -> None:
        self._connection().put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    def _get(self, key: str) -> bytes:
        try:
            response = self._connection().get_object(Bucket=self._bucket, Key=key)
        except ClientError as error:
            raise AppError("Stored file could not be read", 404) from error

        return response["Body"].read()

    def _delete(self, key: str) -> None:
        self._connection().delete_object(Bucket=self._bucket, Key=key)
