import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.config import get_settings

# Load environment variables from root .env file
root_env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=root_env_path, override=True)

settings = get_settings()

app = FastAPI(
    title="Analytics Assistant API",
    openapi_url=f"{settings.api_prefix}/openapi.json",
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
combined_agent = None


@app.on_event("startup")
async def startup_event():
    """Initialize the Combined Agent on startup."""
    global combined_agent
    try:
        from app.services.TTS_vis import CombinedAgent
        print("🔄 Initializing Combined Agent (Text-to-SQL + Visualization)...")
        combined_agent = CombinedAgent()
        print("✅ Combined Agent initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize Combined Agent: {str(e)}")
        # Don't fail startup, just log the error
        combined_agent = None


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global combined_agent
    combined_agent = None
    print("👋 Combined Agent shut down")


app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "agent_status": "ready" if combined_agent is not None else "not_initialized"
    }
