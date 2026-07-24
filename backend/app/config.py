from enum import StrEnum
from functools import lru_cache
from urllib.parse import parse_qs, urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LOCAL_DATABASE_URL = "sqlite:///./fitness.db"
LOCAL_JWT_SECRET = "local-development-secret-change-me-123456"
LOCAL_INVITE_CODE = "FIT-DEMO-2026"


class AppEnvironment(StrEnum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


def normalize_database_url(value: str) -> str:
    value = value.strip()
    if value.startswith("postgres://"):
        return f"postgresql+psycopg://{value.removeprefix('postgres://')}"
    if value.startswith("postgresql://"):
        return f"postgresql+psycopg://{value.removeprefix('postgresql://')}"
    return value


def _split_list(value: object) -> object:
    if isinstance(value, str) and not value.lstrip().startswith("["):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


class Settings(BaseSettings):
    # Environment files are intentionally not loaded implicitly. Local Compose passes
    # values as process environment variables, and deployed services must do the same.
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    app_name: str = "Fitness Intelligence Platform"
    app_env: AppEnvironment = AppEnvironment.LOCAL
    database_url: str = LOCAL_DATABASE_URL
    migration_database_url: str | None = None
    database_sslmode: str | None = None
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_max_overflow: int = Field(default=5, ge=0, le=100)
    database_pool_timeout: int = Field(default=30, ge=1, le=120)
    database_pool_recycle: int = Field(default=1800, ge=30, le=86400)
    database_connect_timeout: int = Field(default=5, ge=1, le=30)
    jwt_secret: str = Field(default=LOCAL_JWT_SECRET, min_length=32)
    access_token_minutes: int = Field(default=480, ge=5, le=1440)
    cors_origins: list[str] | str = ["http://localhost:5175"]
    trusted_hosts: list[str] | str = ["localhost", "127.0.0.1", "testserver"]
    api_docs_enabled: bool = True
    seed_demo_data: bool = False
    demo_mode_enabled: bool = False
    demo_session_minutes: int = Field(default=30, ge=5, le=120)
    demo_coach_email: str = "demo.coach@fitness.example.com"
    demo_trainee_email: str = "demo.trainee@fitness.example.com"
    demo_invite_code: str = LOCAL_INVITE_CODE
    coach_registration_code: str | None = None
    media_storage_provider: str = "local"
    media_local_root: str = "./media"
    media_max_bytes: int = Field(default=5 * 1024 * 1024, ge=1024, le=52_428_800)
    # Demonstration videos are larger than images but still modest — no streaming or
    # transcoding is performed, so this bounds a single short clip stored as-is.
    media_max_video_bytes: int = Field(
        default=25 * 1024 * 1024, ge=1024, le=209_715_200
    )
    log_level: str = "INFO"
    port: int = Field(default=8000, ge=1, le=65535)

    @field_validator("database_url", "migration_database_url", mode="before")
    @classmethod
    def normalize_urls(cls, value: object) -> object:
        return normalize_database_url(value) if isinstance(value, str) else value

    @field_validator("cors_origins", "trusted_hosts", mode="before")
    @classmethod
    def split_lists(cls, value: object) -> object:
        return _split_list(value)

    @field_validator("cors_origins")
    @classmethod
    def normalize_origins(cls, value: list[str] | str) -> list[str]:
        items = [value] if isinstance(value, str) else value
        return list(dict.fromkeys(item.rstrip("/") for item in items if item))

    @field_validator("trusted_hosts")
    @classmethod
    def normalize_hosts(cls, value: list[str] | str) -> list[str]:
        items = [value] if isinstance(value, str) else value
        return list(dict.fromkeys(item.lower() for item in items if item))

    @field_validator("database_sslmode")
    @classmethod
    def valid_sslmode(cls, value: str | None) -> str | None:
        allowed = {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}
        if value is not None and value not in allowed:
            raise ValueError(f"DATABASE_SSLMODE must be one of {', '.join(sorted(allowed))}")
        return value

    @field_validator("log_level")
    @classmethod
    def valid_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR, or CRITICAL")
        return normalized

    @field_validator("demo_coach_email", "demo_trainee_email")
    @classmethod
    def normalize_demo_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized or "@" not in normalized:
            raise ValueError("Demo account identifiers must be email addresses")
        return normalized

    @model_validator(mode="after")
    def secure_deployed_environment(self) -> "Settings":
        if self.demo_coach_email == self.demo_trainee_email:
            raise ValueError("Demo coach and trainee accounts must be distinct")
        if self.app_env not in {AppEnvironment.STAGING, AppEnvironment.PRODUCTION}:
            return self
        errors: list[str] = []
        if self.database_url.startswith("sqlite"):
            errors.append("DATABASE_URL must use PostgreSQL")
        if self.migration_database_url and self.migration_database_url.startswith("sqlite"):
            errors.append("MIGRATION_DATABASE_URL must use PostgreSQL")
        if self.jwt_secret == LOCAL_JWT_SECRET:
            errors.append("JWT_SECRET must not use the local development value")
        if not self.cors_origins or any(
            origin == "*" or not origin.startswith("https://") for origin in self.cors_origins
        ):
            errors.append("CORS_ORIGINS must contain explicit HTTPS origins")
        if not self.trusted_hosts or "*" in self.trusted_hosts:
            errors.append("TRUSTED_HOSTS must contain explicit host names")
        if self.api_docs_enabled:
            errors.append("API_DOCS_ENABLED must be false")
        if self.app_env is AppEnvironment.PRODUCTION and self.seed_demo_data:
            errors.append("SEED_DEMO_DATA must be false in production")
        if self.app_env is AppEnvironment.PRODUCTION and self.demo_mode_enabled:
            errors.append("DEMO_MODE_ENABLED must be false in production")
        if (
            self.app_env is AppEnvironment.PRODUCTION
            and self.media_storage_provider.strip().lower() == "local"
        ):
            # Local media lives on an ephemeral filesystem; production must use a
            # durable object store. Staging may keep local media (synthetic, disposable).
            errors.append(
                "MEDIA_STORAGE_PROVIDER must be a durable provider in production"
            )
        if self.demo_invite_code == LOCAL_INVITE_CODE:
            errors.append("DEMO_INVITE_CODE must not use the public local value")
        sslmode = self.database_sslmode or self._url_sslmode(self.database_url)
        if sslmode not in {"require", "verify-ca", "verify-full"}:
            errors.append("DATABASE_SSLMODE must require TLS")
        if errors:
            raise ValueError("; ".join(errors))
        return self

    @staticmethod
    def _url_sslmode(url: str) -> str | None:
        return parse_qs(urlsplit(url).query).get("sslmode", [None])[0]

    @property
    def effective_migration_database_url(self) -> str:
        return self.migration_database_url or self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
