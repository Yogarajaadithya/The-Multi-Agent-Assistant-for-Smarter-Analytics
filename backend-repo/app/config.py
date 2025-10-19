from typing import List
from functools import lru_cache
from pydantic import BaseModel


class Settings(BaseModel):
    """Application configuration."""
    app_name: str = "Analytics Assistant Backend"
    api_prefix: str = "/api"
    allowed_origins: List[str] = ["http://localhost:5174"]
    lmstudio_base_url: str = "http://127.0.0.1:1234/v1"
    lmstudio_api_key: str = "lm-studio"
    lmstudio_model_id: str = "deepseek/deepseek-r1-0258-qwen3-8b"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
