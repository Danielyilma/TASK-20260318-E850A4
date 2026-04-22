# Activity Registration and Funding Audit Management Platform

This repository implements the platform in phased milestones.

- **Phase 1** delivers a runnable FastAPI + Vue + PostgreSQL scaffold with Docker Compose, Alembic migrations, automated DB checks on startup, and automated tests.
- **Phase 2** adds the core `users`, `activities`, and minimal `registrations` schema (for activity delete rules), JWT auth (`POST /api/v1/auth/login`, `POST /logout`, `GET /me`), full Activities CRUD per `docs/api-spec.md`, a seeded system administrator account, and a Vue UI to authenticate and browse/create activities against the live API.

## Prerequisites

- Docker and Docker Compose
- (Optional, for local development without Docker) Node.js 20+, Python 3.11+, and PostgreSQL 15+

## Environment variables

Copy `.env.example` to `.env` and adjust values for local runs. Compose overrides most settings for containers.

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy connection string for the API |
| `CORS_ORIGINS` | Comma-separated browser origins allowed by the API |
| `JWT_SECRET_KEY` | HS256 signing secret for JWT access tokens |
| `SYSTEM_ADMIN_USERNAME` / `SYSTEM_ADMIN_PASSWORD` | Bootstrap system admin user created by `python -m app.scripts.seed_admin` |
| `VITE_API_BASE_URL` | Optional explicit API base (`/api/v1`) for the Vue app |
| `VITE_DEV_ADMIN_USERNAME` | Optional default username hint for the Activities sign-in form |
| `TEST_DATABASE_URL` | Optional pytest database URL (defaults to in-memory SQLite) |

## Run with Docker Compose

From the repository root:

```bash
docker compose up --build
```

Wait until all services are healthy, then verify:

- API health: `curl -s http://localhost:8000/api/v1/health` → `{"status":"ok"}`
- UI: open `http://localhost:5173` — the home page loads **live** health from the backend (no mocked API in the app).
- Activities UI: open `http://localhost:5173/activities` and sign in with the seeded administrator (`admin` / `AdminP@ss1` by default unless you changed compose env vars).

The backend entrypoint waits for PostgreSQL, runs `alembic upgrade head`, runs `python -m app.scripts.seed_admin`, then starts Uvicorn on port **8000**. The frontend runs the Vite dev server on port **5173**.

Stop services:

```bash
docker compose down
```

## Local development (without Docker)

### Database

Start PostgreSQL and create a database matching `DATABASE_URL` (defaults to `postgresql://app:app@localhost:5432/app`).

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://app:app@localhost:5432/app
alembic upgrade head
python -m app.scripts.seed_admin
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Ensure `CORS_ORIGINS` includes your Vite origin (defaults include `http://localhost:5173`).

## Tests

### Backend (pytest)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

By default tests use an isolated in-memory SQLite database with `StaticPool` so no external database is required. Set `TEST_DATABASE_URL` to exercise PostgreSQL instead.

### Frontend (Vitest)

```bash
cd frontend
npm install
npm run test:unit
```

## Project layout (Phase 2)

- `backend/app` — FastAPI modular monolith (`api`, `core`, `models`, `schemas`, `services`, `repositories`, `scripts`)
- `backend/alembic` — migrations (`users`, `activities`, `registrations`)
- `frontend/src` — Vue app with Router + Pinia, centralized Axios client, `services/*.service.js`, and activity views

## API contract notes

Global error handling follows the standard envelope from `docs/api-spec.md` (`{ "error": { "code", "message" } }`).

Implemented endpoints in this milestone include:

- `GET /api/v1/health`
- `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`, `GET /api/v1/auth/me`
- `POST /api/v1/activities` (system admin)
- `GET /api/v1/activities` (authenticated)
- `GET /api/v1/activities/{activity_id}` (authenticated)
- `PUT /api/v1/activities/{activity_id}` (system admin)
- `DELETE /api/v1/activities/{activity_id}` (system admin; soft delete with registration conflict checks)
