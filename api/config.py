from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().with_name(".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = Field(default="OnMe", alias="APP_NAME")
    app_version: str = Field(default="0.2.0", alias="APP_VERSION")
    environment: Literal["local", "staging", "production"] = Field(
        default="local",
        alias="ENVIRONMENT",
    )
    database_url: str = Field(alias="DATABASE_URL")
    jwt_secret: SecretStr = Field(alias="JWT_SECRET")
    replicate_api_key: SecretStr = Field(alias="REPLICATE_API_KEY")
    asset_storage_path: Path = Field(
        default=Path("./local_uploads"),
        alias="ASSET_STORAGE_PATH",
    )
    allowed_origins_raw: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="ALLOWED_ORIGINS",
    )
    port: int = Field(default=8000, alias="PORT", ge=1, le=65535)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme != "postgresql+asyncpg":
            raise ValueError(
                "DATABASE_URL must use the 'postgresql+asyncpg' scheme."
            )
        if not parsed.hostname:
            raise ValueError("DATABASE_URL must include a hostname.")
        if not parsed.path or parsed.path == "/":
            raise ValueError("DATABASE_URL must include a database name.")
        return value

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: SecretStr) -> SecretStr:
        secret = value.get_secret_value().strip()
        insecure_values = {
            "changeme",
            "secret",
            "dev-secret-change-in-production",
        }
        if len(secret) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long.")
        if secret.lower() in insecure_values:
            raise ValueError("JWT_SECRET must not use a known insecure default.")
        return value

    @field_validator("replicate_api_key")
    @classmethod
    def validate_replicate_api_key(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("REPLICATE_API_KEY is required.")
        return value

    @field_validator("allowed_origins_raw")
    @classmethod
    def validate_allowed_origins(cls, value: str) -> str:
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        if not origins:
            raise ValueError("ALLOWED_ORIGINS must include at least one origin.")
        if any(origin == "*" for origin in origins):
            raise ValueError("ALLOWED_ORIGINS must not contain '*'.")
        return ",".join(origins)

    @property
    def uploads_dir(self) -> Path:
        return self.asset_storage_path / "uploads"

    @property
    def results_dir(self) -> Path:
        return self.asset_storage_path / "results"

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.allowed_origins_raw.split(",")
            if origin.strip()
        ]

    @property
    def JWT_SECRET(self) -> str:
        return self.jwt_secret.get_secret_value()

    @property
    def REPLICATE_API_TOKEN(self) -> str:
        return self.replicate_api_key.get_secret_value()

    @property
    def UPLOAD_DIR(self) -> str:
        return str(self.uploads_dir)

    @property
    def RESULTS_DIR(self) -> str:
        return str(self.results_dir)

    @property
    def DATABASE_PATH(self) -> str:
        return str(self.asset_storage_path / "legacy.sqlite3")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        raise RuntimeError(
            "Application boot blocked by invalid environment configuration.\n"
            f"{exc}"
        ) from exc


settings = get_settings()
