# C12 Verification Conformance

## Scope

This corrective change closes the C12 gaps identified by the C00 audit. It
does not add a browser driver, OpenGame execution, Promote, Publish or
Workspace UI.

## Evidence gate

- Platform verdicts are `PASSED`, `PARTIAL_FAILURE`, `CRITICAL_FAILURE`, and
  `INVALID`.
- Evidence records include `source` and `severity`.
- The service persists a platform-owned Build Check and requires Browser Smoke,
  Core Gameplay Acceptance, and a validated `window.__GAME_TEST__` hook.
- Runtime-only PASS, contradictory reports, missing checks and unsafe artifact
  references remain non-ready.
- Failed and invalid reports are idempotent and never update the current
  Playable pointer.
- Repair links increment both candidate attempt and `repair_round`; the fourth
  link is rejected after three repair rounds.

## Verification commands

```bash
VENV=/Users/zhaozhuo/workspace/explore/ai-cowork-game/.worktrees/platform-backend-foundation/backend/.venv/bin
"$VENV/pytest" backend/tests/test_c12_schema.py backend/tests/test_c12_candidate_test_gate.py backend/tests/test_c12_candidate_api.py -q
"$VENV/pytest" backend/tests -q
npm ci --prefix frontend
npm run build --prefix frontend
git diff --check
```

## Results

- Focused C12: `20 passed, 1 warning`.
- Full backend: `122 passed, 1 warning`.
- Alembic upgrade to `0010_c12_verification_conformance` ran twice against
  the same temporary SQLite database without error.
- Frontend `vue-tsc -b` and Vite build passed (`1664 modules transformed`).
- The only warning is the existing Starlette/httpx TestClient deprecation.
