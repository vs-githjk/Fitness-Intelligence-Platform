from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    app_name: str = "Fitness Intelligence Platform"
    database_url: str = "sqlite:///./fitness.db"
    jwt_secret: str = Field(default="local-development-secret-change-me-123456", min_length=32)
    access_token_minutes: int = 480
    cors_origins: list[str] | str = ["http://localhost:5173"]
    demo_invite_code: str = "FIT-DEMO-2026"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str) and not value.startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
