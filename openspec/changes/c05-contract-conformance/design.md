## Context

The merged foundation has one mutable `GameDesign` row per Project and immutable-content `GameSpecRevision` rows. Existing `/design` and `/gamespec` endpoints are already consumed by the Vue prototype and must remain recognizable. See `proposal.md` and the C00 audit for the motivation and conformance gap.

## Goals / Non-Goals

**Goals:**

- Preserve current API routes while making GDD content revisioned and confirmed content immutable.
- Store clarification and readiness data with a revision so refresh/resume is deterministic.
- Keep FastAPI as the only owner of Confirm GDD and Confirm GameSpec.
- Preserve provider-neutral CreatorGameSpec and explicit GDD → GameSpec provenance.
- Give each migration, service operation and API behavior a focused regression test.

**Non-Goals:**

- No Build, OpenGame, Candidate verification, Human Promote, Publish or Resource Review behavior.
- No Vue visual redesign and no migration of the entire `projectStore` in this Change.
- No new workflow engine, queue, worker, Pinia or Vue Router.

## Decisions

### 1. Add a revision table and retain the Project aggregate

Create `game_design_revisions` with `project_id`, `revision_number`, `content_json`, `readiness_json`, `status`, timestamps and confirmation metadata. Keep `game_designs` as the project-level aggregate used by existing lifecycle code, adding current/confirmed revision pointers instead of replacing the table.

Alternative considered: turning `game_designs` itself into a multi-row revision table. Rejected because it would invalidate the existing unique project relation and API queries across C02-C04; the aggregate-plus-history model keeps the migration additive.

### 2. Readiness is structured contract data

Add a strict `DesignReadiness` model with `status`, `blockers`, `unresolved_decisions` and `checked_at`. The API accepts persisted readiness from the design collaboration layer but the service enforces the final gate: only `ready` can be confirmed. No timer or frontend status can confirm it.

### 3. Save creates a revision; confirm changes lifecycle status only

`submit_design` creates a new draft revision and updates the aggregate's current pointer. It never edits the JSON of a revision that is already confirmed. `confirm_design` verifies the current revision belongs to the Project, is valid and ready, then marks it confirmed and supersedes the previous confirmed pointer in one transaction.

### 4. GameSpec stores source provenance without embedding workflow state

Add `source_design_revision_id` to `game_spec_revisions`. The field is relational provenance, not a CreatorGameSpec property. The GameSpec API remains independently confirmable and its content is still validated through `CreatorGameSpec` before confirmation.

### 5. Compatibility-first response expansion

Keep existing response fields (`design_id`, `status`, `draft`, `revision_id`, `revision_number`, `spec`) and add nullable/current revision metadata and readiness. Existing clients can continue rendering while newer clients use the new fields.

## Risks / Trade-offs

- [Existing rows have no revision history] → migration backfills one revision from each current `GameDesign` row and points the aggregate at it; unknown readiness is `not_ready` with an explicit migration blocker.
- [A stale client confirms an old draft] → service checks the current revision pointer and Project ownership before confirming.
- [The frontend sends legacy draft payloads without readiness] → default readiness to `not_ready`, preserving data while requiring an explicit readiness update before confirmation.
- [GameSpec is saved before GDD confirmation] → keep draft persistence for editing, but block confirmation/build and require a confirmed source revision.

## Migration Plan

1. Add `game_design_revisions` and nullable aggregate/source columns in one Alembic revision.
2. Backfill one draft revision per existing `game_designs` row, preserving JSON and timestamps.
3. Deploy service/API changes and run repository/API tests against an empty database and a migrated database.
4. Rollback is migration-only before dependent rows are created; after deployment, preserve history and use a forward migration rather than deleting confirmed revisions.

## Open Questions

None. Readiness defaults and compatibility behavior are fixed above for this Change.
