# Run Event Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist ordered run events and expose replayable status/SSE endpoints without restarting builds on refresh.

**Architecture:** SQLAlchemy models and migration store one Run row plus uniquely sequenced RunEvent rows. A
repository owns idempotent creation, sequence checks, sanitization, terminal transitions, cancellation, and
orphan recovery. A thin FastAPI router exposes create/status/replay/stream/cancel and never parses provider logs.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2, Alembic, SQLite, pytest, SSE `StreamingResponse`.

## Global Constraints

- Same `run_id` must be reused on refresh/reconnect; no endpoint creates a new run from an event replay.
- Provider events are normalized C06 `RunEvent` values; raw logs and secrets are not persisted or returned.
- Terminal success is explicit and cannot be inferred from disconnect, timer, or event text alone.
- No OpenGame parsing, BuildCandidate promotion, Workspace UI, queue, worker, or new dependency.

---

### Task 1: Run/Event persistence schema

**Files:**
- Modify: `backend/app/models.py`
- Create: `backend/migrations/versions/0004_run_event_observability.py`
- Test: `backend/tests/test_c07_run_events.py`

**Interfaces:**
- `Run` and `RunEventRecord` models with unique `(run_id, sequence)` and terminal status fields.

- [ ] **Step 1: Write failing migration/model tests** for run table, event table, exact sequence uniqueness, and
  idempotent run identity.
- [ ] **Step 2: Run the focused tests and verify the new models/table imports fail.**
- [ ] **Step 3: Add models and repeatable Alembic migration without changing existing tables.**
- [ ] **Step 4: Run migration and focused tests, then the existing backend suite.**
- [ ] **Step 5: Commit `feat: persist runs and ordered events`.**

### Task 2: Run repository and terminal rules

**Files:**
- Create: `backend/app/repositories/runs.py`
- Modify: `backend/app/repositories/__init__.py`
- Modify: `backend/app/contracts/game_agent.py`
- Test: `backend/tests/test_c07_run_events.py`

**Interfaces:**
- `RunRepository.create_run(run_id, build_id)`.
- `RunRepository.get_run(run_id)` and `list_events(run_id, after_sequence)`.
- `RunRepository.append_event(event)` with exact next sequence.
- `RunRepository.finish_run(run_id, status, terminal_event)`.
- `RunRepository.request_cancel(run_id)` and `recover_orphaned_runs()`.

- [ ] **Step 1: Add failing repository tests** for ordered append/replay, secret redaction, terminal guards,
  cancellation, orphan recovery, and success requiring a confirmed terminal artifact event.
- [ ] **Step 2: Run focused tests and verify repository imports/behavior fail.**
- [ ] **Step 3: Implement minimal repository transaction methods and bounded diagnostic sanitization.**
- [ ] **Step 4: Run focused and full backend tests.**
- [ ] **Step 5: Commit `feat: add run event repository`.**

### Task 3: REST status, replay, cancel, and SSE

**Files:**
- Create: `backend/app/api/runs.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_c07_run_api.py`

**Interfaces:**
- `POST /api/v1/runs`.
- `GET /api/v1/runs/{run_id}`.
- `GET /api/v1/runs/{run_id}/events`.
- `GET /api/v1/runs/{run_id}/events/stream`.
- `POST /api/v1/runs/{run_id}/cancel`.

- [ ] **Step 1: Write failing API tests** for idempotent create, persisted status, JSON replay, SSE replay from
  `Last-Event-ID`, and cancellation without false success.
- [ ] **Step 2: Run focused API tests and verify route failures.**
- [ ] **Step 3: Implement the thin router and bounded SSE polling generator with terminal/idle close.**
- [ ] **Step 4: Run API and full backend tests.**
- [ ] **Step 5: Commit `feat: expose run status and event replay`.**

### Task 4: Verification and documentation

**Files:**
- Modify: `docs/superpowers/plans/2026-08-14-run-event-observability.md`
- Modify: `docs/development/V1_CHANGE_CATALOG.md`

- [ ] **Step 1: Mark completed plan steps and review for scope leakage.**
- [ ] **Step 2: Run `pytest backend/tests -q`, `npm --prefix frontend run build`, and `git diff --check`.**
- [ ] **Step 3: Manually curl create/status/replay/cancel and parse SSE IDs from a terminal run.**
- [ ] **Step 4: Commit `docs: record run event observability verification`.**
