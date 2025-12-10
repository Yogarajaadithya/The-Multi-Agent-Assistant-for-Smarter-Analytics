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
    
    # Azure OpenAI Configuration
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "https://assistant-genai.openai.azure.com/")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
    azure_openai_deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")
    
    # Database configuration
    db_schema: str = os.getenv("DB_SCHEMA", "public")
    db_table: str = os.getenv("DB_TABLE", "wa_fn_usec")
    
    def __init__(self, **kwargs):
        # Override with environment variables if present
        env_origins = os.getenv("ALLOWED_ORIGINS")
        if env_origins:
            kwargs["allowed_origins"] = [origin.strip() for origin in env_origins.split(",")]
        
        super().__init__(**kwargs)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
