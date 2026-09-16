"""Application configuration loaded from environment variables.

Uses pydantic-settings for typed, validated configuration with safe local
defaults for development. No secrets are ever committed to the repository.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    app_name: str = "OrthoVision AI"
    app_env: str = "development"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # --- Storage ---
    # Root directory for all persisted artifacts (DICOM, volumes, models, exports).
    storage_dir: str = "./storage"

    # Storage backend: "local" (filesystem) or "s3" (S3-compatible object
    # storage such as Supabase Storage, Cloudflare R2, AWS S3, or MinIO).
    storage_backend: str = "local"

    # --- Object storage (only used when storage_backend == "s3") ---
    s3_bucket_name: str = ""
    s3_endpoint_url: str = ""
    s3_region: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""

    # --- Upload limits ---
    max_upload_size_bytes: int = 2 * 1024 * 1024 * 1024  # 2 GiB total per upload
    max_files_per_upload: int = 5000

    # --- Database ---
    database_url: str = "sqlite:///./orthovision.db"

    # --- Job queue ---
    # "local" (in-process threads) or "redis" (RQ + Redis for production).
    job_backend: str = "local"
    redis_url: str = "redis://localhost:6379/0"
    redis_queue: str = "orthovision"

    # --- CORS ---
    cors_origins: str = "http://localhost:3000"

    # --- Processing ---
    default_reconstruction_threshold_hu: int = 300
    max_reconstruction_kwargs: dict | None = None

    @property
    def storage_path(self) -> Path:
        return Path(self.storage_dir)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
