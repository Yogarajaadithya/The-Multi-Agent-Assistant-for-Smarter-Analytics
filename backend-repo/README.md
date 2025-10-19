# FastAPI Backend

## Features

- `/health` endpoint for quick readiness checks.
- `/api/chat` endpoint that forwards the user query to an LM Studio server.
- CORS configured for the React frontend dev server.

## Prerequisites

- Python 3.11+ (recommended)
- LM Studio running locally (optional for development) or another server that exposes a chat-completions compatible API.

## Setup

```bash
cd backend-repo
python -m venv .venv
.\.venv\Scripts\activate  # (PowerShell) use `source .venv/bin/activate` on bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration

Environment variables:

- `APP_NAME` – overrides the title in docs.
- `API_PREFIX` – change the base path (default `/api`).
- `ALLOWED_ORIGINS` – comma-separated list for CORS.
- `LM_STUDIO_URL` – base URL for LM Studio (default `http://localhost:1234`).
- `LM_STUDIO_MODEL` – model identifier (default `lmstudio-community/Meta-Llama-3-8B-Instruct`).
- `LM_TEMPERATURE` – sampling temperature (default `0.2`).
- `LM_MAX_TOKENS` – max tokens per response (default `512`).
- `LM_REQUEST_TIMEOUT` – request timeout in seconds (default `30`).

Store them in `.env` and load via `python-dotenv` or your process manager.

## Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000 with documentation at `/docs`.

## Connecting to LM Studio

LM Studio exposes an OpenAI-compatible API when you enable the server feature. Make sure it is running and reachable at `LM_STUDIO_URL` (default `http://localhost:1234`). The backend will forward chat requests to `/v1/chat/completions`.
