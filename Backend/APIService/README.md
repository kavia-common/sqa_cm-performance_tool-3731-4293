# Backend/APIService (FastAPI)

This folder contains a FastAPI bootstrap for the **SQA_CM Performance Tool** backend API.

## Implemented endpoints (v1)

All endpoints are mounted under the `/v1` prefix:

- `GET /v1/metrics/current` → returns `EnvelopeCurrentMetrics` (placeholder metrics)
- `GET /v1/health` → returns `EnvelopeHealth` (placeholder dependency health)
- `GET /v1/ready` → returns `EnvelopeReady`

Interactive API docs are available at `/docs` (and OpenAPI JSON at `/openapi.json`).

## Preview / frontend interaction

The React frontend (running on port **3000**) should call the API using the configured base URL:

- `REACT_APP_API_BASE` / `REACT_APP_BACKEND_URL` should point to the API host (commonly `:8000` in preview).

CORS is configured to allow:
- `http://localhost:3000`
- `REACT_APP_FRONTEND_URL` (if set)

## Configuration (env)

This backend **reuses existing REACT_APP_* variables** already present in the workspace. Additional common hosting env vars are supported:

- `HOST` (default `0.0.0.0`)
- `PORT` (default `8000`)
- `LOG_LEVEL` (fallback to `REACT_APP_LOG_LEVEL`, default `info`)

No changes are made to CI/preview processes by this bootstrap.
