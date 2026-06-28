from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[4]


@lru_cache
def read_platform_version() -> str:
    version_file = ROOT_DIR / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "1.0.0"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ParsLex API"
    debug: bool = True
    api_prefix: str = "/api/v1"

    database_url: str = "postgresql://parslex:parslex@localhost:5432/parslex"
    secret_key: str = "dev-secret-change-in-production"
    access_token_expire_minutes: int = 480
    algorithm: str = "HS256"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "parslex"
    minio_secret_key: str = "parslexsecret"
    minio_bucket: str = "parslex-documents"
    minio_secure: bool = False

    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # AI — parametric model config (see config/ai/models.yaml)
    ai_models_config: str = "config/ai/models.yaml"
    ollama_base_url: str = "http://localhost:11434"

    default_admin_email: str = "admin@parslex.com"
    default_admin_password: str = "admin123"
    default_admin_name: str = "Platform Admin"

    @property
    def app_version(self) -> str:
        return read_platform_version()

    @property
    def ai_models_config_path(self) -> Path:
        path = Path(self.ai_models_config)
        if path.is_absolute():
            return path
        return ROOT_DIR / path


settings = Settings()
