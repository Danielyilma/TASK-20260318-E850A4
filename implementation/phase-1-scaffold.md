## Phase 1: Scaffold (Foundation)

### Goals
- Establish the base project structure for the full-stack application.
- Set up the FastAPI backend and Vue.js frontend environments.
- Configure PostgreSQL database and Alembic for migrations.
- Containerize the application using Docker and Docker Compose for local development.
- Initialize testing frameworks and ensure CI/CD readiness.

### Backend Implementation
1. **Initialize Python Project:** Create a `backend` directory, set up a virtual environment, and initialize `requirements.txt` with FastAPI, Uvicorn, SQLAlchemy, Alembic, psycopg2-binary, and python-dotenv.
2. **Project Structure:** Create the standard directory layout (`app/api`, `app/core`, `app/models`, `app/schemas`, `app/services`).
3. **Database Configuration:** Set up SQLAlchemy database connection in `app/core/database.py` using `.env` variables.
4. **Alembic Setup:** Run `alembic init` and configure `env.py` to target the base SQLAlchemy metadata for auto-generating migrations.
5. **Health Check Endpoint:** Create a basic `GET /api/v1/health` endpoint that checks database connectivity and returns a 200 OK.
6. **Backend Dockerfile:** Write a `Dockerfile` for the FastAPI backend using a lightweight Python base image (e.g., `python:3.11-slim`), configuring port 8000.

### Frontend Implementation
1. **Initialize Vue Project:** Run `npm create vue@latest` (or Vite) in a `frontend` directory. Select Vue Router and Pinia during setup.
2. **Project Structure:** Organize folders (`src/views`, `src/components`, `src/stores`, `src/services`, `src/layouts`).
3. **API Client Setup:** Install `axios` and create a base client instance in `src/services/api.js` configured to hit the backend API (e.g., `http://localhost:8000/api/v1`).
4. **Routing Setup:** Configure `src/router/index.js` with basic root and placeholder views (`Home.vue`, `NotFound.vue`).
5. **Basic Layout:** Create a root `App.vue` that contains a router-view and basic navigation skeleton.
6. **Frontend Dockerfile:** Write a `Dockerfile` using Node for building, and possibly a lightweight nginx container or Vite config for serving locally on port 5173.

### Infrastructure / DevOps
1. **Docker Compose:** Create a `docker-compose.yml` defining services:
   - `db`: PostgreSQL 15+ container, volume-mapped, with health checks.
   - `backend`: FastAPI container, depending on `db`, parsing `.env`.
   - `frontend`: Vue.js container for serving the frontend application.
2. **.gitignore:** Create a comprehensive `.gitignore` preventing `.env`, `__pycache__`, `node_modules`, and local SQLite/media files from being committed.
3. **README.md:** Provide clear, step-by-step instructions on setting up environment variables, running `docker-compose up --build`, and verifying setup manually.

### Testing Plan
- **Backend Setup Tools:** `pytest`, `pytest-asyncio`, `httpx`.
- **Frontend Setup Tools:** `vitest`, `@vue/test-utils`.
- **Tasks:**
  - Write a `pytest` fixture to spin up a test database.
  - Implement a backend test: `test_health_endpoint` asserting a 200 status code.
  - Implement a frontend test: `test_app_renders` verifying `App.vue` mounts successfully via Vitest.

### Definition of Done
- `docker-compose up` cleanly starts all three containers without crashing.
- `GET http://localhost:8000/api/v1/health` returns `{ "status": "ok" }`.
- Frontend is accessible at `http://localhost:5173`.
- Backend backend tests pass via `pytest`.
- Frontend tests pass via `npm run test:unit`.
