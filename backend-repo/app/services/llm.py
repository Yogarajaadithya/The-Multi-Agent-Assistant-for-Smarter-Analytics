from openai import OpenAI, AsyncOpenAI
from app.config import Settings, get_settings

def get_lm_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(
        base_url=settings.lmstudio_base_url,
        api_key=settings.lmstudio_api_key,
    )
