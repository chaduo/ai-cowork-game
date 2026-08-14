# C11 Build Job Orchestration Verification

## Automated evidence

- Backend: `pytest backend/tests -q` -> 80 passed, 1 existing Starlette/httpx deprecation warning.
- Frontend: `npm --prefix frontend run build` -> `vue-tsc -b` and Vite build passed.
- Focused C11 tests cover stable IDs, duplicate create (`201` then `200`), confirmed-input and baseline capture, active guard, FakeGameAgent success/failure/timed_out/unsupported/cancelled, diagnostics persistence, retry ancestry, current playable immutability, API query and orphan recovery.

## Boundary review

- BuildService consumes only `GameBuildRequest`, `GameBuildResult`, `RunEvent` and the `GameAgent` protocol.
- No OpenGame command, subprocess, raw log parsing, TestReport, Promote, Publish, or Workspace UI was added.
- Startup lifespan calls orphan recovery so active Run/Build records do not remain in `running` after a backend restart.

## Known prototype limitation

The C11 API uses `FakeGameAgent` and executes it synchronously in the request because real provider execution belongs to C09/C10. C11 deliberately does not claim real OpenGame artifact generation.
