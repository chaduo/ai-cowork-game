## Why

The merged C05 foundation persists a mutable `GameDesign` row and a `GameSpecRevision`, but it cannot preserve confirmed GDD history or unresolved design readiness across refreshes. This blocks the V1 rule that GDD and GameSpec are separate Human Confirm gates and that confirmed design content is immutable.

## What Changes

- Add immutable, project-scoped GDD revision records for draft and confirmed design content.
- Persist clarification state, unresolved decisions and readiness blockers with the current GDD revision.
- Make design saves create new draft revisions instead of overwriting a confirmed revision.
- Require readiness to be `ready` before Confirm GDD; keep the existing design API paths compatible while exposing revision metadata.
- Associate each GameSpec revision with the confirmed GDD revision used to produce it and preserve immutable content snapshots.
- Reject GameSpec confirmation when the design gate is not confirmed, the draft is invalid, or a newer draft has unresolved validation errors.
- Keep all provider commands, workspace paths, resource workflow state and UI state outside CreatorGameSpec.

## Capabilities

### New Capabilities

- `design-revision-readiness`: Immutable GDD revisions, clarification persistence, readiness validation and independent Confirm GDD behavior.

### Modified Capabilities

- None. The existing C00 governance capability remains the authority; this Change adds the C05 implementation contract.

## Impact

- Adds a SQLite migration and SQLAlchemy model/repository/service behavior for GDD revisions.
- Extends design and GameSpec API response metadata without removing existing fields.
- Adds API/service/contract tests for immutable revisions, refresh recovery, readiness blocking and GameSpec provenance.
- Does not implement Build, OpenGame, Candidate verification, resources or Vue business state migration.
