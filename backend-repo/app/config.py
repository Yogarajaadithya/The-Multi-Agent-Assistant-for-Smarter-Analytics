import os
from typing import List
from functools import lru_cache
from pydantic import BaseModel, Field, ValidationError


class Settings(BaseModel):
    """Application configuration derived from environment variables."""
    class Config:
        validate_assignment = True

    app_name: str = Field(
        default="Analytics Assistant Backend",
        description="Human-friendly name for OpenAPI docs."
    )
    api_prefix: str = Field(default="/api", description="Base path for API routes.")
    allowed_origins: List[str] = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174"
        ],
        description="CORS origins permitted to call the API."
    )
    lm_studio_url: str = Field(
        default="http://localhost:1234",
        description="Base URL for the LM Studio REST API (no trailing slash)."
    )
    lm_studio_model: str = Field(
        default="lmstudio-community/Meta-Llama-3-8B-Instruct",
        description="Model identifier exposed by LM Studio."
    )
    lm_temperature: float = Field(
        default=0.2,
        ge=0,
        le=2,
        description="Sampling temperature for completions."
    )
    lm_max_tokens: int = Field(
        default=512,
        gt=0,
        description="Maximum tokens for each completion."
    )
    lm_request_timeout: float = Field(
        default=30.0,
        gt=0,
        description="Timeout (seconds) for LM Studio HTTP requests."
    )

    @classmethod
    def from_env(cls) -> "Settings":
        raw = {
            "app_name": os.getenv("APP_NAME"),
            "api_prefix": os.getenv("API_PREFIX"),
            "allowed_origins": _split_list(os.getenv("ALLOWED_ORIGINS")),
            "lm_studio_url": os.getenv("LM_STUDIO_URL"),
            "lm_studio_model": os.getenv("LM_STUDIO_MODEL"),
            "lm_temperature": _optional_float(os.getenv("LM_TEMPERATURE")),
            "lm_max_tokens": _optional_int(os.getenv("LM_MAX_TOKENS")),
            "lm_request_timeout": _optional_float(os.getenv("LM_REQUEST_TIMEOUT")),
        }
        # Remove keys where env var was not provided so defaults are used.
        filtered = {k: v for k, v in raw.items() if v not in (None, [], "")}
        try:
            return cls(**filtered)
        except ValidationError as exc:
            raise RuntimeError(f"Invalid environment configuration: {exc}") from exc


def _split_list(value: str | None) -> List[str] | None:
    if value is None:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def _optional_float(value: str | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    return int(value)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
