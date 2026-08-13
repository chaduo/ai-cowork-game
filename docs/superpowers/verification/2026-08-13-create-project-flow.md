# C03 Create Project Flow Verification

## Scope

C03 persists a Project from the user's Idea, exposes create/list/get API routes, supports
Idempotency-Key retries, and passes the stable Project ID into the existing K01 → Creative
Kickoff → K02 flow. It does not generate Game Design/GameSpec or add Build/OpenGame behavior.

## Fresh Evidence

```text
../platform-backend-foundation/backend/.venv/bin/pytest backend/tests -q
24 passed, 1 warning

Alembic upgrade head twice
tables include projects, game_designs, game_spec_revisions, builds,
build_candidates, playable_versions, releases, alembic_version
projects includes idempotency_key

cd frontend && npx vue-tsc -b && npx vite build
exit 0
```

## Covered Acceptance

- Blank or whitespace-only Idea is rejected with the C01 error envelope.
- `POST /api/v1/projects` persists the original Idea and returns a stable Project ID.
- Repeating the same `Idempotency-Key` returns the same Project instead of duplicating it.
- A new key is independent, so equal Idea text is not incorrectly treated as a global unique key.
- `GET /api/v1/projects` and `GET /api/v1/projects/{id}` support refresh/reload recovery.
- K01 creates the backend Project before opening the existing Creative Kickoff modal.
- Kickoff confirmation passes the persisted Project ID to the existing local session so K02 opens that Project.
- Existing visual/Kickoff flow remains in place; no Game Design generation was added.

## Boundary Note

The prototype still keeps rich K02 session data in the existing local store. C03 only makes
Project identity and original Idea real and durable; later Changes will migrate the richer
domain payloads and workspace reads incrementally.
