# C10/C13 Corrective Design

**Date:** 2026-08-16  
**Status:** Approved for implementation  
**Scope:** Correctness fixes for the merged C10 OpenGame adapter and C13 workspace isolation.

## Goal

Make the merged C10/C13 baseline conform to the provider-neutral contract and its approved adapter design without changing Project persistence, BuildService ownership, or provider selection wiring.

## Decisions

- The OpenGame prompt is deterministic and includes the canonical `RuntimeBuildSpec`, first-playable validation, and approved build-context fields. It never includes workspace host paths or credentials.
- Malformed stream-json is an `invalid_output` result even when a later result event says success.
- Artifact validation returns every regular file under the approved workspace, with normalized relative paths, bounded manifest size, file kind, size, and SHA-256. `index.html` is the only valid preview entry.
- Cancellation requested before the executor starts or while it is active produces `cancelled`; a process that has already completed naturally remains completed even if its result is still being drained.
- One `OpenGameAdapter` owns one C09 executor and therefore rejects a second active run with an explicit busy error.
- Symlink checks happen before canonical containment checks so the policy reports `symlink_escape` consistently.

## Non-goals

- No real OpenGame wiring into the FastAPI app.
- No container/network/CPU policy, Candidate promotion, publishing, or Vue changes.
- No new provider-specific fields in `GameBuildRequest`, `GameBuildResult`, `RunEvent`, or `BuildService`.

## Verification

Add focused regression tests first, then run the C10/C13 suites, the full backend suite, and the existing frontend typecheck/build.
