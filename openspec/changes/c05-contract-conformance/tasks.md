## 1. Contract and migration tests

- [x] 1.1 Add failing schema tests for `DesignReadiness`, revision metadata and legacy payload defaulting to `not_ready`.
- [x] 1.2 Add failing migration tests for `game_design_revisions`, aggregate pointers and `game_spec_revisions.source_design_revision_id` from an empty and a pre-C05 database.
- [x] 1.3 Add failing service/API tests for save-as-new-draft, immutable confirmed content, readiness blocking, refresh recovery and independent GameSpec confirmation.

## 2. Persistence and domain implementation

- [x] 2.1 Add `GameDesignRevision` and the aggregate/source pointer columns to SQLAlchemy models and create Alembic migration `0007_c05_design_revisions`.
- [x] 2.2 Backfill existing GameDesign rows as `not_ready` draft revisions without changing their JSON content or timestamps.
- [x] 2.3 Add strict readiness and revision DTOs while keeping existing design/GameSpec response fields compatible.
- [x] 2.4 Update lifecycle service actions so design save creates a revision, confirm checks current ownership/readiness, and GameSpec save captures confirmed GDD provenance.

## 3. API and regression verification

- [x] 3.1 Extend design/GameSpec responses with revision/readiness/source metadata and map readiness errors to the existing API error envelope.
- [x] 3.2 Run the focused C05 tests through red-green-refactor and add cross-project isolation/duplicate-confirm coverage.
- [x] 3.3 Run migration repeatability, full backend tests, frontend typecheck/build and OpenSpec strict validation.
- [x] 3.4 Record evidence and confirm Out of Scope surfaces (Build/OpenGame/Candidate/Resource/Vue business state) were not modified.
