"""Validated service configuration."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="LAYA_", extra="ignore")

    host: str = "0.0.0.0"
    port: int = Field(default=8089, ge=1, le=65535)
    log_level: str = "info"
    device: Literal["auto", "cpu", "cuda", "mps", "xpu"] = "auto"
    models: tuple[str, ...] = ("english", "multilingual")
    revision: str | None = None
    preload: bool = True
    max_loaded: int = Field(default=2, ge=1, le=3)
    auto_task_detection: bool = False
    threads: int | None = Field(default=None, ge=1)
    max_concurrent: int = Field(default=4, ge=1, le=128)
    max_body_bytes: int = Field(default=2_000_000, ge=1_024, le=100_000_000)
    max_state_chars: int = Field(default=50_000, ge=1, le=1_000_000)
    max_questions: int = Field(default=100, ge=1, le=1_000)
    max_batch_states: int = Field(default=64, ge=1, le=1_000)
    max_token_budget: int = Field(default=8_192, ge=128, le=16_384)
    api_key: SecretStr | None = None
    cors_origins: tuple[str, ...] = ()

    @field_validator("models", "cors_origins", mode="before")
    @classmethod
    def split_csv(cls, value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            return tuple(item.strip() for item in value.split(",") if item.strip())
        return tuple(value) if value else ()


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
