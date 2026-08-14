# C11 Build Context Corrective Design

**Date:** 2026-08-14
**Status:** Approved for implementation
**Base:** `origin/main` at `beb8985`

## Goal

Make every Build carry one immutable, provider-ready context snapshot. The snapshot must prove exactly which confirmed GameSpec, baseline Playable, affected scope, accepted resource references, implementation dependencies and overrides produced a Candidate.

## Decisions

1. Add a `BuildContext` record with one-to-one ownership by `Build`. It stores canonical JSON snapshots and SHA-256 hashes for the CreatorGameSpec and RuntimeBuildSpec, plus task-scoped context and provenance JSON. The record is created before the first provider call and is never updated.
2. `BuildService.create_build` creates the context inside the same transaction as the Build and Run. Existing idempotent requests return the existing context; a conflicting retry cannot replace it.
3. `GameBuildRequest` is reconstructed from the stored context, never from later Project or GameSpec state. New context values use explicit C06 contract types; implementation dependencies are stored as a bounded list of stable strings until a dedicated dependency contract exists.
4. `BuildCandidate` stores the immutable `build_context_id`. Candidate creation remains success-only and current Playable is untouched.
5. Retry creates a new Build and a new immutable context copied from the original context. The original context remains unchanged and the new context records the parent build id through the existing Build relation.
6. No resource backend, OpenGame adapter, verification gate, promotion, publish, or Workspace UI is added in C11.

## Data model

`build_contexts`:

- `id`, `build_id` (unique), `project_id`
- `gamespec_revision_id`, `gamespec_snapshot_json`, `gamespec_snapshot_hash`
- `runtime_build_spec_json`, `runtime_build_spec_hash`
- `baseline_playable_version_id`, `affected_scope_json`
- `resource_references_json`, `implementation_dependencies_json`, `relevant_overrides_json`
- `game_design_profile_json`, `gamespec_profile_json`, `game_build_profile_json`
- `operation`, `request_text`, `context_hash`, `created_at`

`build_candidates.build_context_id` is a required foreign key for new rows and is populated by C11 success handling. Existing rows are backfilled from their Build context during migration.

## Invariants

- A context can be read after refresh/restart and its hashes remain stable.
- Later edits to Project current playable or a newer GameSpec revision cannot alter an existing context or Candidate provenance.
- Duplicate Build creation with the same stable id never calls the provider twice and never creates a second context.
- Failed, cancelled, timed-out, invalid-output and unsupported results do not create or mutate a Candidate context pointer.
- A successful Build creates exactly one Candidate linked to its context and does not set `Project.current_playable_version_id`.
