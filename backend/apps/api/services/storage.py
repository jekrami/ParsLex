import hashlib
import io
from uuid import UUID, uuid4

from minio import Minio
from minio.error import S3Error

from apps.api.core.config import settings


class ObjectStorageService:
    def __init__(self) -> None:
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket = settings.minio_bucket

    def ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def upload(self, org_id: UUID, file_name: str, content: bytes, content_type: str) -> tuple[str, str]:
        self.ensure_bucket()
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
        try:
            response = self.client.get_object(self.bucket, storage_key)
            data = response.read()
            content_type = response.headers.get("Content-Type") if response.headers else None
            response.close()
            response.release_conn()
            return data, content_type
        except S3Error as exc:
            raise FileNotFoundError(storage_key) from exc


storage_service = ObjectStorageService()
