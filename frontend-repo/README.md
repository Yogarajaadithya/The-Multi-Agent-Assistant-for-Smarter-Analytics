# Frontend React Chat Bot

## Prerequisites

- Node.js 18+ (consider using `nvm`/`nvs` to manage versions)
- npm or yarn

## Setup

```bash
cd frontend-repo
npm install
```

## Development

```bash
npm run dev
```

The dev server defaults to http://localhost:5173 and proxies API calls from `/api` to the FastAPI backend. Set `BACKEND_URL` in `.env` or export `VITE_BACKEND_URL` if the backend runs on another host.

## Build

```bash
npm run build
```

Static assets are emitted to `dist/`. Serve them with any static host (e.g., `npm run preview`).
