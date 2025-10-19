# The-Multi-Agent-Assistant-for-Smarter-Analytics

AI-powered system that can understand natural-language questions and perform automated descriptive, diagnostic, and what-if analyses on HR data. By integrating multiple specialized agents for data exploration, statistical validation, and visualization, the assistant provides explainable, interactive insights.

## Project layout

- `frontend-repo/` – Vite/React single-page app that captures a user query and calls the FastAPI backend.
- `backend-repo/` – FastAPI service that proxies chat requests to an LM Studio server (OpenAI-compatible API).

## Quick start

1. **Backend**
   ```bash
   cd backend-repo
   python -m venv .venv
   .\.venv\Scripts\activate  # or `source .venv/bin/activate`
   pip install -r requirements.txt
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   Ensure LM Studio (or any OpenAI-compatible endpoint) is reachable at the URL defined in `LM_STUDIO_URL`.

2. **Frontend**
   ```bash
   cd frontend-repo
   npm install
   npm run dev
   ```
   The frontend dev server runs on http://localhost:5173 and proxies `/api` calls to the backend.

Adjust `.env` / `.env.example` files in each project to customize ports, models, and origins.
