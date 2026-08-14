# C11 Build Context Corrective Plan

## Task 1: Red persistence and immutability tests

- [x] Add tests for the `build_contexts` table, canonical hashes, duplicate Build idempotency and context reload.
- [x] Add tests proving later GameSpec/current playable changes do not mutate stored context.
- [x] Add tests for resource references, affected scope, implementation dependencies, overrides and provider request mapping.
- [x] Add tests for Candidate-to-context linkage and retry context ancestry.

## Task 2: Persist immutable Build Context

- [x] Add `BuildContext` model and repeatable migration.
- [x] Add `build_context_id` to `BuildCandidate` with nullable compatibility for existing legacy candidates.
- [x] Implement canonical JSON/hash helpers and context creation/read methods.

## Task 3: Wire BuildService to the stored context

- [x] Capture context atomically before provider invocation.
- [x] Reconstruct `GameBuildRequest` only from the immutable context.
- [x] Preserve context on duplicate execution and copy it for retry without mutating the parent.
- [x] Link BuildCandidate creation to the context; keep current Playable unchanged.

## Task 4: Verification

- [x] Run focused C11 tests, full backend tests, migration repeatability and frontend build.
- [x] Record evidence and update `c11-build-context-conformance.md` and the V1 catalog.
- [x] Confirm no OpenGame, TestReport, Promote, Publish, Resource Review or Workspace UI files changed.
