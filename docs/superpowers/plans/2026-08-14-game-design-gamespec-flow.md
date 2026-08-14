# Game Design / GameSpec Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task with verification checkpoints.

**Goal:** Persist recoverable Game Design clarification and canonical CreatorGameSpec revisions, require independent Human Confirm gates, and expose a validated input contract for RuntimeBuildSpec without moving resource workflow state into GameSpec.

**Architecture:** Reuse the C02 `GameDesign` and `GameSpecRevision` rows with typed JSON contracts. A small design-flow API owns draft persistence and confirmation; `ProjectLifecycleService` remains the only lifecycle mutation boundary and rejects Build until the confirmed design and canonical GameSpec are valid. Vue keeps short-lived loading, selected-section, and modal state local while mapping the existing Chinese Prototype ViewModel to/from the canonical contract.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, pytest, Vue 3, TypeScript, existing Vite/Vue toolchain.

## Global Constraints

- Do not add Pinia, Vue Router, backend APIs beyond this flow, workflow engines, queues, workers, or runtime dependencies.
- Keep `recommended`, `dismissed`, `used`, drawer state, and resource ids out of `CreatorGameSpec` and `GameSpecRevision.content_json`.
- Preserve the existing Chinese-first Workspace/K01/K02 visual language and component structure.
- A Game Design Confirm and a GameSpec Confirm are separate Human Gates.
- Every task ends with focused tests plus `backend/.venv/bin/pytest backend/tests -q`, `cd frontend && npx vue-tsc -b && npx vite build` when frontend files are involved.

---

### Task 1: Canonical contracts and prototype mapping

**Files:**
- Create: `backend/app/contracts/gamespec.py`
- Create: `backend/tests/test_c05_gamespec_contract.py`
- Create: `frontend/src/contracts/creatorGameSpec.ts`
- Create: `frontend/src/contracts/creatorGameSpecMapping.ts`
- Create: `frontend/src/contracts/creatorGameSpecMapping.test.ts` (plain exported assertions only if the repository test runner is unavailable)
- Modify: `frontend/src/components/workspace/workspaceTypes.ts` only when a shared type alias is needed.

**Interfaces:**
- `CreatorGameSpec` contains `schema_version`, `title`, `first_playable`, `gameplay`, `characters`, `rules`, `scope`, and `validation`.
- `CreatorGameSpec.characters` requires `relationship_growth`, `favor_rules`, `relationship_events`, and `request_rewards`.
- `RuntimeBuildSpec` is a separate read-only mapping output containing only build-relevant canonical fields.
- `creatorGameSpecFromViewModel(model: GameSpecModel): CreatorGameSpec` and `gameSpecViewModelFromCreator(spec: CreatorGameSpec, fallback: GameSpecModel): GameSpecModel` are pure functions.

- [ ] **Step 1: Write failing backend contract tests** for a valid Chinese prototype payload, missing relationship fields, and workflow keys being rejected or ignored rather than persisted.
- [ ] **Step 2: Run** `../platform-backend-foundation/backend/.venv/bin/pytest backend/tests/test_c05_gamespec_contract.py -q` and confirm the new contract import/validation fails.
- [ ] **Step 3: Implement** the Pydantic models with bounded strings/lists and a `to_runtime_build_spec()` method that never reads resource workflow keys.
- [ ] **Step 4: Add frontend mapping tests** that round-trip the farm and coffee fixtures and assert relationship fields survive.
- [ ] **Step 5: Implement** the TypeScript mapping with explicit field-by-field copies; do not serialize the entire ViewModel object.
- [ ] **Step 6: Run focused backend tests and the frontend typecheck** and confirm green.
- [ ] **Step 7: Commit** `feat: add creator gamespec contracts`.

### Task 2: Persistable Game Design draft and API

**Files:**
- Create: `backend/app/contracts/design.py`
- Create: `backend/app/api/design.py`
- Create: `backend/tests/test_c05_design_api.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/services/lifecycle.py`

**Interfaces:**
- `CreatorGameDesignDraft` includes `schema_version`, `original_idea`, `project_title`, `scenario_id`, `summary`, `decisions`, and `clarification` (`question_index`, `status`, `custom_input`).
- `PUT /api/v1/projects/{project_id}/design` validates and upserts `GameDesign.content_json`, sets status `submitted`, and returns the saved draft plus status.
- `GET /api/v1/projects/{project_id}/design` returns the persisted draft or a deterministic draft derived from Project Original Idea without creating a confirmation.
- `POST /api/v1/projects/{project_id}/design/confirm` only succeeds for a submitted draft and sets `confirmed_at`/`status=confirmed`.

- [ ] **Step 1: Write failing API tests** for save/refresh restore, idempotent overwrite, missing project, and independent design confirmation.
- [ ] **Step 2: Run** the focused tests and confirm the router/schema behavior is missing.
- [ ] **Step 3: Implement** the typed draft contract and API router using the existing `ApiError` envelope and `ProjectLifecycleService` transaction style.
- [ ] **Step 4: Add lifecycle methods** `save_design_draft`, `get_design_draft`, and `confirm_design` while preserving C02 stage derivation.
- [ ] **Step 5: Run** focused and full backend tests.
- [ ] **Step 6: Commit** `feat: persist game design drafts and confirmation`.

### Task 3: Canonical GameSpec revisions, validation, and confirmation

**Files:**
- Create: `backend/tests/test_c05_gamespec_api.py`
- Modify: `backend/app/api/design.py`
- Modify: `backend/app/services/lifecycle.py`
- Modify: `backend/app/contracts/gamespec.py`

**Interfaces:**
- `GET /api/v1/projects/{project_id}/gamespec` returns the latest revision and its validation/status metadata.
- `PUT /api/v1/projects/{project_id}/gamespec` validates `CreatorGameSpec`, creates the next `GameSpecRevision` with `status=draft`, and never changes the current playable pointer.
- `POST /api/v1/projects/{project_id}/gamespec/confirm` confirms only a valid draft revision whose Game Design is confirmed; prior confirmed revisions become superseded.
- `ProjectLifecycleService.validate_gamespec_revision(revision_id)` returns structured validation errors.

- [ ] **Step 1: Write failing tests** for create revision, invalid relationship payload, revision numbering, refresh restore, confirmation precondition, and supersede behavior.
- [ ] **Step 2: Run focused tests and verify red.**
- [ ] **Step 3: Implement** validation and revision endpoints using `CreatorGameSpec.model_validate_json`/`model_validate` and the existing transaction scope.
- [ ] **Step 4: Return structured field details** through the existing API error envelope; no raw Pydantic traceback reaches the client.
- [ ] **Step 5: Run all backend tests and confirm C02 expectations are updated only where the canonical contract intentionally changed.
- [ ] **Step 6: Commit** `feat: validate and confirm canonical gamespec revisions`.

### Task 4: Enforce Build gate and RuntimeBuildSpec input contract

**Files:**
- Create: `backend/tests/test_c05_build_gate.py`
- Modify: `backend/app/services/lifecycle.py`
- Modify: `backend/tests/test_c02_build_service.py` and any fixture that currently uses a non-canonical GameSpec.

**Interfaces:**
- `start_build` must require a confirmed GameDesign and a confirmed, schema-valid GameSpec revision.
- `ProjectLifecycleService.runtime_build_spec(project_id)` returns a `RuntimeBuildSpec` derived only from the confirmed canonical GameSpec.

- [ ] **Step 1: Write failing tests** for unconfirmed design, invalid GameSpec, confirmed design + confirmed valid GameSpec, and workflow metadata not appearing in RuntimeBuildSpec.
- [ ] **Step 2: Run focused tests and confirm current `start_build` incorrectly allows at least one blocked case.
- [ ] **Step 3: Implement the gate in the service before Build row creation; preserve active-build and current-playable invariants.
- [ ] **Step 4: Update shared C02 fixtures to use the canonical test payload rather than weakening the new invariant.
- [ ] **Step 5: Run the full backend suite and migration checks.
- [ ] **Step 6: Commit** `feat: gate builds on confirmed gamespec`.

### Task 5: API client and frontend mapping integration

**Files:**
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/stores/projectStore.ts`
- Modify: `frontend/src/components/workspace/workspaceTypes.ts` only for explicit canonical metadata types.
- Create: `frontend/src/contracts/creatorGameSpecMapping.ts` if Task 1 did not create it.

**Interfaces:**
- `getProjectDesign`, `saveProjectDesign`, `confirmProjectDesign`.
- `getProjectGameSpec`, `saveProjectGameSpec`, `confirmProjectGameSpec`.
- `projectStore` keeps `designDraftStatus`, `gamespecStatus`, and request errors as UI-facing state only; canonical payloads remain API responses.

- [ ] **Step 1: Add focused TypeScript compile fixtures** for API response shapes and mapping round-trips.
- [ ] **Step 2: Implement the API client with snake_case JSON conversion matching the FastAPI contract.
- [ ] **Step 3: Add store actions that update the active session’s local ViewModel only after API success, preserving resource matching fields.
- [ ] **Step 4: Run** `cd frontend && npx vue-tsc -b` and the backend suite.
- [ ] **Step 5: Commit** `feat: connect frontend design and gamespec APIs`.

### Task 6: Persist clarification and independent Game Design confirmation in K01

**Files:**
- Modify: `frontend/src/components/kickoff/CreativeKickoffModal.vue`
- Modify: `frontend/src/screens/K01CreateProject.vue`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/api/client.ts` if request types need refinement.

**Interfaces:**
- The modal emits deterministic draft snapshots while answering clarification and a confirmed design payload only after Human Confirm.
- K01 saves draft snapshots using the stable backend Project ID and restores them when reopening the kickoff flow.
- `App.enterWorkspace` calls `confirmProjectDesign` before starting local generation; a failed confirmation keeps the user in the design flow and does not start GameSpec/build.

- [ ] **Step 1: Add a failing component-level behavior fixture** (or a small pure event serializer test if no Vue test runner exists) proving a selected choice becomes a recoverable draft payload.
- [ ] **Step 2: Implement modal draft emission without moving API calls into the visual choice components.
- [ ] **Step 3: Wire K01/App to debounce-free save-on-transition and restore-on-open calls; show Chinese loading/error copy.
- [ ] **Step 4: Ensure closing/reopening does not reset decisions for the same Project ID.
- [ ] **Step 5: Run frontend typecheck/build and full backend tests.
- [ ] **Step 6: Commit** `feat: persist clarification and confirm game design`.

### Task 7: Persist, edit, and confirm GameSpec in K02

**Files:**
- Modify: `frontend/src/screens/K02ProjectWorkspace.vue`
- Modify: `frontend/src/components/workspace/GameSpecDocument.vue`
- Modify: `frontend/src/stores/projectStore.ts`
- Modify: `frontend/src/App.vue` for load/restore orchestration.

**Interfaces:**
- K02 loads the latest canonical revision when opening a Project with a confirmed Game Design.
- Existing section editing still uses `SpecContext`; save maps the ViewModel to a new draft revision.
- “确认规格并开始构建” first calls `confirmProjectGameSpec`; only a successful response can call the existing local build timeline.
- Invalid/blocked responses remain in the GameSpec view with an actionable error message and do not change phase/current playable.

- [ ] **Step 1: Add a failing integration fixture** for mapping an edited characters section to the canonical relationship fields and for blocked confirm.
- [ ] **Step 2: Implement load/save/confirm actions at the K02 container boundary; keep `GameSpecDocument` presentational.
- [ ] **Step 3: Preserve `originalRelationshipDraft`/resource workflow fields outside canonical payloads.
- [ ] **Step 4: Run typecheck/build and full backend tests.
- [ ] **Step 5: Commit** `feat: connect gamespec confirmation to workspace`.

### Task 8: Verification record and acceptance walkthrough

**Files:**
- Create: `docs/superpowers/verification/2026-08-14-game-design-gamespec-flow.md`

- [ ] **Step 1: Run** `../platform-backend-foundation/backend/.venv/bin/pytest backend/tests -q`.
- [ ] **Step 2: Run** `cd frontend && npx vue-tsc -b && npx vite build` using the worktree dependency tree or the existing local dependency tree without changing package metadata.
- [ ] **Step 3: Run migration upgrade twice against a temporary SQLite database.
- [ ] **Step 4: Exercise API acceptance with curl/TestClient: create Project, save clarification, confirm design, save invalid GameSpec, save valid GameSpec, confirm GameSpec, attempt Build before/after gates, and restart client to restore drafts.
- [ ] **Step 5: Exercise UI acceptance: create Project, answer clarification, close/reopen, confirm Game Design, edit GameSpec relationship fields, refresh, confirm GameSpec, verify Build begins only afterward, and verify resource workflow keys are absent from API payloads.
- [ ] **Step 6: Write exact commands, pass counts, and any environment caveat in the verification document.
- [ ] **Step 7: Commit** `docs: record game design gamespec verification`.
