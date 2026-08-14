# C01 Platform Backend Foundation Verification

## Scope

This Change implements only the FastAPI/SQLite foundation. It does not create Project,
GameSpec, Build, Release, Resource, OpenGame, SSE, queue, worker or workflow-engine behavior.

## Fresh Evidence

From the C01 worktree:

```text
./backend/.venv/bin/pytest -q
10 passed, 1 warning

DATABASE_URL=sqlite:///.../.db ./backend/.venv/bin/alembic -c backend/alembic.ini upgrade head
DATABASE_URL=sqlite:///.../.db ./backend/.venv/bin/alembic -c backend/alembic.ini upgrade head
tables: [('alembic_version',)]

cd frontend && npx vue-tsc -b && npx vite build
exit 0
```

The warning is emitted by the installed FastAPI/Starlette TestClient compatibility layer;
it does not fail the suite.

Direct backend smoke on a temporary port returned:

```json
{"status":"ok","service":"ai-cowork-game-api","version":"0.1.0"}
```

and included an `X-Request-ID` response header.

The configured default port 8000 already had another local process returning 404, so that
process was not killed or treated as C01. The Vite proxy is compile-verified; its end-to-end
`/api/healthz` smoke should be run after the existing port-8000 process is stopped.

## Stage Coverage

- FastAPI app + health: app factory and `/healthz`, tested with `TestClient`.
- Config: `APP_ENV`, `DATABASE_URL`, `LOG_LEVEL` defaults and environment overrides.
- Database connection: SQLAlchemy SQLite engine open/close.
- Migrations: Alembic, environment override, repeatable upgrade, no domain tables.
- Repository/transaction: commit on success, rollback on exception.
- Error envelope: validation and unexpected errors with safe details and request id.
- Test database: unique temporary SQLite fixture with migrations and cleanup.
- Vue API client/proxy: typed health/error client and `/api` Vite proxy.

## Deferred to Later Changes

- Project domain schema and lifecycle repositories belong to C02.
- OpenGame process behavior belongs to C08-C10.
- Event/SSE observability belongs to C07.
- Business API routes and Human Gates belong to later Changes.
