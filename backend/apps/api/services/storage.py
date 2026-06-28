import hashlib
import io
import mimetypes
from pathlib import Path
from uuid import UUID, uuid4

from apps.api.core.config import settings


class StorageBackend:
    def ensure_ready(self) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def upload(self, org_id: UUID, file_name: str, content: bytes, content_type: str) -> tuple[str, str]:  # pragma: no cover - interface
        raise NotImplementedError

    def download(self, storage_key: str) -> tuple[bytes, str | None]:  # pragma: no cover - interface
        raise NotImplementedError


class LocalStorageBackend(StorageBackend):
    """Filesystem-backed storage for local dev without MinIO/Docker."""

    def __init__(self) -> None:
        self.root = settings.storage_local_path_resolved

    def ensure_ready(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def upload(self, org_id: UUID, file_name: str, content: bytes, content_type: str) -> tuple[str, str]:
        self.ensure_ready()
        content_hash = hashlib.sha256(content).hexdigest()
        storage_key = f"{org_id}/{uuid4()}/{file_name}"
        target = self.root / storage_key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return storage_key, content_hash

    def download(self, storage_key: str) -> tuple[bytes, str | None]:
        target = self.root / storage_key
        if not target.exists():
            raise FileNotFoundError(storage_key)
        content_type, _ = mimetypes.guess_type(str(target))
        return target.read_bytes(), content_type


class MinioStorageBackend(StorageBackend):
    """Object-storage backend (production / full Docker stack)."""

    def __init__(self) -> None:
        from minio import Minio

        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket = settings.minio_bucket

    def ensure_ready(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def upload(self, org_id: UUID, file_name: str, content: bytes, content_type: str) -> tuple[str, str]:
        self.ensure_ready()
        content_hash = hashlib.sha256(content).hexdigest()
        storage_key = f"{org_id}/{uuid4()}/{file_name}"
        self.client.put_object(
            self.bucket,
            storage_key,
            io.BytesIO(content),
            length=len(content),
            content_type=content_type,
        )
        return storage_key, content_hash

    def download(self, storage_key: str) -> tuple[bytes, str | None]:
        from minio.error import S3Error

        try:
            response = self.client.get_object(self.bucket, storage_key)
            data = response.read()
            content_type = response.headers.get("Content-Type") if response.headers else None
            response.close()
            response.release_conn()
            return data, content_type
        except S3Error as exc:
            raise FileNotFoundError(storage_key) from exc


def _build_storage() -> StorageBackend:
    if settings.storage_provider.lower() == "minio":
        return MinioStorageBackend()
    return LocalStorageBackend()


storage_service: StorageBackend = _build_storage()
