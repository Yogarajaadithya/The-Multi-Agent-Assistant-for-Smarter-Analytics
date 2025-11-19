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

# Global LLM instance
llm_instance = None


@app.on_event("startup")
async def startup_event():
    """Initialize the Multi-Agent System on startup."""
    global llm_instance
    try:
        from app.services.multi_agent_system import initialize_llm
        print("[INFO] Initializing Multi-Agent System...")
        print("   - Planner Agent (Question Router)")
        print("   - Text-to-SQL + Visualization Agents")
        print("   - Hypothesis + Statistical Testing Agents")
        llm_instance = initialize_llm()
        print("[SUCCESS] Multi-Agent System initialized successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Multi-Agent System: {str(e)}")
        import traceback
        traceback.print_exc()
        # Don't fail startup, just log the error
        llm_instance = None


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global llm_instance
    llm_instance = None
    print("[INFO] Multi-Agent System shut down")


app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "agent_status": "ready" if llm_instance is not None else "not_initialized"
    }
