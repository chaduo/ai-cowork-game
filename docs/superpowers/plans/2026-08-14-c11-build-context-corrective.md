# C11 Build Context Corrective Plan

## Task 1: Red persistence and immutability tests

- Add tests for the `build_contexts` table, canonical hashes, duplicate Build idempotency and context reload.
- Add tests proving later GameSpec/current playable changes do not mutate stored context.
- Add tests for resource references, affected scope, implementation dependencies, overrides and provider request mapping.
- Add tests for Candidate-to-context linkage and retry context ancestry.

## Task 2: Persist immutable Build Context

- Add `BuildContext` model and repeatable migration.
- Add `build_context_id` to `BuildCandidate` with a safe backfill for existing candidates.
- Implement canonical JSON/hash helpers and create/read repository methods.

## Task 3: Wire BuildService to the stored context

- Capture context atomically before provider invocation.
- Reconstruct `GameBuildRequest` only from the immutable context.
- Preserve context on duplicate execution and copy it for retry without mutating the parent.
- Link successful Candidate creation to the context; keep current Playable unchanged.

## Task 4: Verification

- Run focused C11 tests, full backend tests, migration repeatability and frontend build.
- Record evidence and update `c11-build-context-conformance.md` and the V1 catalog.
- Confirm no OpenGame, TestReport, Promote, Publish, Resource Review or Workspace UI files changed.
