# C06/C07 Corrective Contract Design

**Date:** 2026-08-14
**Status:** Approved for implementation
**Base:** `origin/main` at `b906bdc`

## Goal

Close the provider-neutral contract gaps identified by the V1 conformance audit without rewriting the already merged C06/C07 foundations. A Build request must carry complete task-scoped context, and a Run must preserve a provider-requested user decision across refresh, reconnect, and backend restart.

## C06 contract

`GameBuildRequest` keeps the existing project/build/spec/workspace fields and adds:

- `affected_scope`: named sections and a human-readable scope description.
- `resource_references`: accepted resource id, revision, source project and snapshot provenance.
- `relevant_overrides`: explicit key/value overrides with source and provenance.
- `game_design_profile`, `gamespec_profile`, and `game_build_profile`: provider-neutral profile name, contract version and capabilities. There is intentionally no Verification Agent profile.

All new collections default to empty values so existing C11 callers remain source-compatible while new adapters can require complete context at their boundary. `CreatorGameSpec` remains the canonical design input and does not receive provider or workflow fields.

`GameBuildStatus` adds the non-terminal `waiting_for_input` state. `GameBuildResult` carries a stable `PendingDecision` when waiting, and continues to require a structured error for terminal non-success statuses. `RunEvent` gains an optional `decision_id`; provider event kinds remain unable to express Promote, Publish, or Resource Review decisions.

## C07 persistence and replay

The database adds `run_pending_decisions`, keyed by `(run_id, decision_id)`, with prompt, input kind, options, status, response and timestamps. `Run` statuses distinguish execution (`running`, `cancelling`) from the non-terminal waiting state (`waiting_for_input`). Waiting runs are not orphaned by backend restart.

`RunRepository` provides:

- `mark_waiting_for_input(run_id, event, decision)` to append `build.needs_input` and persist the pending decision atomically.
- `continue_run(run_id, decision_id, response)` to resolve one decision, append `build.continued`, and return the same run to `running`.
- Existing sequence enforcement and sanitized REST/SSE replay from `after_sequence` / `Last-Event-ID`.

The Run REST response exposes the pending decision. A small input endpoint resolves it; it never creates a second run and never changes Promote/Publish state. SSE keeps the existing bounded polling/replay behavior and emits events in sequence order.

## Error and invariant policy

- Unknown run or decision is a standard API error.
- A decision can only be resolved once and only by the owning run.
- Waiting is non-terminal; `finish_run` rejects terminal completion while a decision is pending.
- Only `running` and `cancelling` runs become orphaned on restart; `waiting_for_input` remains resumable.
- Provider output cannot mutate Project, Candidate, PlayableVersion, Release, or saved resources.

## Out of scope

No OpenGame CLI, subprocess, adapter parser, BuildService redesign, Candidate verification, Promote/Publish API, Workspace UI, queue, worker, Pinia, Vue Router, or new runtime dependency is added.

## Verification

Focused tests will cover request context/profiles, waiting results, forbidden gate events, pending decision persistence, continuation idempotency, restart preservation, REST replay and SSE `Last-Event-ID`. Existing backend tests and frontend build must remain green.
