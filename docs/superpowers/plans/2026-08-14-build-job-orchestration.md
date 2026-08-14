# C11 Build Job Orchestration Plan

## Task 1: Persist build inputs and diagnostics

- Extend Build with operation, request text, and baseline playable pointer.
- Extend BuildCandidate with serialized diagnostics.
- Add a repeatable Alembic migration.
- Add red tests proving confirmed input and diagnostics survive reload.

## Task 2: BuildService over GameAgent contract

- Add `BuildService.create_build`, `execute_build`, `cancel_build`, `retry_build`, and `recover_orphaned_jobs`.
- Use C07 RunRepository for ordered events and terminal state.
- Use only `GameBuildRequest`/`GameBuildResult`/`RunEvent` and FakeGameAgent in tests.
- Add red/green tests for idempotency, active guard, outcomes, retry, and recovery.

## Task 3: Build REST endpoints

- Add create/query/cancel/retry endpoints and response schemas.
- Wire the router without adding UI or new runtime dependencies.
- Add API contract tests for stable identifiers and terminal semantics.

## Task 4: Verification

- Run backend pytest, frontend typecheck/build, and focused API smoke checks.
- Record evidence and update the V1 catalog C11 status.
- Review that no Promote, TestReport, OpenGame subprocess, or Workspace UI behavior entered C11.
