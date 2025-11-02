from typing import List
from functools import lru_cache
from pydantic import BaseModel
import os


class Settings(BaseModel):
    """Application configuration."""
    app_name: str = "Analytics Assistant Backend"
    api_prefix: str = "/api"
    allowed_origins: List[str] = [
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]
    lmstudio_base_url: str = "http://127.0.0.1:1234/v1"
    lmstudio_api_key: str = "lm-studio"
    lmstudio_model_id: str = "ibm/granite-3.2-8b"
    
    def __init__(self, **kwargs):
        # Override with environment variables if present
        env_origins = os.getenv("ALLOWED_ORIGINS")
        if env_origins:
            kwargs["allowed_origins"] = [origin.strip() for origin in env_origins.split(",")]
        
        super().__init__(**kwargs)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
