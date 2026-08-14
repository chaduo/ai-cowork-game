# Platform Backend Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the smallest tested FastAPI + SQLite foundation for C01 without implementing project-domain business behavior.

**Architecture:** A small `backend/app` package owns configuration, FastAPI assembly, database lifecycle, migrations, and shared API errors. Tests use an isolated temporary SQLite database and exercise the same app factory used by local development. The Vue app receives only a proxy and typed health/error client seam; existing pages remain prototype-local.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic settings, SQLite, SQLAlchemy, Alembic, pytest, httpx, Vue 3 + Vite.

## Global Constraints

- Do not create Project, GameSpec, Build, Release, Resource, SSE, queue, worker, or workflow-engine business behavior.
- Keep FastAPI as the future owner of lifecycle and Human Gates; this Change only creates infrastructure primitives.
- Use TDD: every production behavior starts with a failing test and is kept minimal.
- Do not introduce Pinia, Vue Router, backend APIs beyond `/healthz`, or provider/OpenGame-specific runtime code.
- Every completed stage runs its focused tests plus `cd frontend && npx vue-tsc -b && npx vite build`.

---

### Task 1: FastAPI app and health endpoint

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/test_health.py`
- Create: `backend/tests/__init__.py`

**Interfaces:**
- Produces `create_app() -> FastAPI` and `GET /healthz`.

- [ ] Write `test_healthz_returns_ok_payload` using `TestClient(create_app())`; assert status 200 and `status`, `service`, `version` keys.
- [ ] Run `cd backend && pytest tests/test_health.py -q`; expected RED because the app package does not exist.
- [ ] Add the minimal FastAPI app factory and health route with a static local application version.
- [ ] Run the focused test; expected GREEN.
- [ ] Run frontend typecheck/build and commit `feat(c01): add fastapi health endpoint`.

### Task 2: Typed configuration

**Files:**
- Create: `backend/app/config.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_config.py`

**Interfaces:**
- Produces `Settings` and `get_settings() -> Settings`.

- [ ] Write tests for deterministic local defaults and environment override of `APP_ENV`, `DATABASE_URL`, and `LOG_LEVEL`.
- [ ] Run focused config tests and verify RED.
- [ ] Implement minimal typed settings loading with no secret logging and inject settings into app creation.
- [ ] Run focused tests and the health test; expected GREEN.
- [ ] Run frontend checks and commit `feat(c01): add backend configuration`.

### Task 3: SQLite connection lifecycle

**Files:**
- Create: `backend/app/db.py`
- Modify: `backend/app/config.py`
- Create: `backend/tests/test_db.py`

**Interfaces:**
- Produces `create_engine_for(settings)`, `get_connection()`, and an app/test-safe database lifecycle.

- [ ] Write a test that creates a temporary SQLite database, opens it through the configured connection, and closes it cleanly.
- [ ] Run the focused test and verify RED.
- [ ] Implement the smallest SQLAlchemy SQLite engine/session setup; enable SQLite foreign-key pragmas only if needed by the foundation.
- [ ] Run database and health tests; expected GREEN.
- [ ] Run frontend checks and commit `feat(c01): add sqlite connection lifecycle`.

### Task 4: Repeatable migrations

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/migrations/env.py`
- Create: `backend/migrations/script.py.mako`
- Create: `backend/migrations/versions/0001_foundation.py`
- Create: `backend/tests/test_migrations.py`

**Interfaces:**
- Produces the documented migration command `python -m alembic upgrade head` and a migration history with no C02+ tables.

- [ ] Write a test that upgrades a fresh temporary SQLite database twice and inspects the resulting table names/version.
- [ ] Run the migration test and verify RED.
- [ ] Add Alembic wiring and a no-business-table foundation revision.
- [ ] Run the migration test and all backend tests; expected GREEN.
- [ ] Run frontend checks and commit `feat(c01): add repeatable sqlite migrations`.

### Task 5: Repository transaction primitive

**Files:**
- Create: `backend/app/repositories/__init__.py`
- Create: `backend/app/repositories/transaction.py`
- Create: `backend/tests/test_transactions.py`

**Interfaces:**
- Produces `transaction_scope(engine)` context manager with commit on success and rollback on exception.

- [ ] Write a test using a test-only temporary table: a successful scope persists a row; an exception scope leaves no row.
- [ ] Run the focused test and verify RED.
- [ ] Implement the context manager without domain-specific repository classes.
- [ ] Run transaction, migration, health and config tests; expected GREEN.
- [ ] Run frontend checks and commit `feat(c01): add transaction scope`.

### Task 6: Shared API error envelope

**Files:**
- Create: `backend/app/errors.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_errors.py`

**Interfaces:**
- Produces `ApiError` and a stable `{ "error": { "code", "message", "details", "request_id" } }` response for known validation/application/unexpected errors.

- [ ] Write tests for an intentionally raised application error and malformed request input; assert safe envelope and non-empty request id.
- [ ] Run focused tests and verify RED.
- [ ] Add minimal exception handlers and request-id middleware; redact stack traces and database details from responses.
- [ ] Run all backend tests; expected GREEN.
- [ ] Run frontend checks and commit `feat(c01): add api error envelope`.

### Task 7: Isolated test database fixtures

**Files:**
- Create: `backend/tests/conftest.py`
- Modify: `backend/tests/test_db.py`
- Modify: `backend/tests/test_migrations.py`
- Modify: `backend/tests/test_health.py`

**Interfaces:**
- Produces pytest fixtures that create a unique temporary database, apply migrations, construct the app with that database, and never fall back to the developer database.

- [ ] Write an isolation test that mutates the fixture database and proves a second test gets a clean database.
- [ ] Run it and verify RED.
- [ ] Implement fixtures and app factory override hooks.
- [ ] Run the complete backend test suite; expected GREEN.
- [ ] Run frontend checks and commit `test(c01): isolate backend test database`.

### Task 8: Vue API client and Vite proxy

**Files:**
- Modify: `frontend/vite.config.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/client.test.ts` only if the existing frontend test runner is established; otherwise add a typed compile-safe module and a documented curl/proxy smoke check.
- Modify: `backend/tests/test_health.py` only if a cross-origin/proxy contract assertion is needed.

**Interfaces:**
- Produces `getHealth(): Promise<HealthResponse>` and typed `ApiClientError` parsing for the `/healthz` endpoint through `/api` proxy mapping.

- [ ] Write the smallest client contract test or compile-time contract fixture and verify RED if a test runner exists.
- [ ] Add the Vite proxy and fetch client without changing existing page routing or state.
- [ ] Run the frontend build and a manual proxy smoke command against both dev servers.
- [ ] Run all backend tests and frontend checks; expected GREEN.
- [ ] Commit `feat(c01): add frontend api client seam`.

### Task 9: C01 verification and handoff

**Files:**
- Create: `docs/superpowers/verification/2026-08-13-platform-backend-foundation.md`
- Modify: `docs/change-briefs/platform-backend-foundation.md` only for evidence links/status.

- [ ] Run `cd backend && pytest -q` and the documented migration command against a temporary database.
- [ ] Run `cd frontend && npx vue-tsc -b && npx vite build`.
- [ ] Verify no C02+ domain tables or OpenGame/runtime code entered the diff.
- [ ] Record exact commands, pass counts, health response, migration repeatability, rollback, error envelope, test isolation and proxy smoke evidence.
- [ ] Ask zhang for required review, then commit `docs(c01): record backend foundation verification`.

