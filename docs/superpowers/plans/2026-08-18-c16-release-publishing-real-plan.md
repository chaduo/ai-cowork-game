# C16 Real Release Publishing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Each task ends with a focused verification cycle.

**Goal:** Replace the Release prototype's local publish state with a persisted Publish Review → Human Publish → immutable Release flow.

**Architecture:** Extend the existing SQLAlchemy lifecycle model and C20 checkpoint wrapper without moving business gates into Vue. Add a small Release REST surface and map it into the existing `ProjectSession`; keep modal/drawer state local while release records and extraction batch summaries come from the backend.

**Tech Stack:** FastAPI, SQLAlchemy/Alembic, pytest/TestClient, Vue 3, TypeScript, existing fetch API client and Vite build.

## Global Constraints

- No Pinia, Vue Router, backend APIs outside the existing FastAPI app, queue, worker, or runtime dependency.
- Human Publish remains an explicit user action; no provider event or timer may create a Release.
- A failed or repeated Publish must not mutate the current Playable or create a second Release.
- Resource extraction in C16 creates only an honest empty/ready batch summary; ResourceCandidate persistence belongs to C17.
- Preserve existing calm Workspace visual language and demo screen compatibility.

---

### Task 1: Persist immutable Release snapshot and extraction batch

**Files:**
- Create: `backend/migrations/versions/0015_c16_release_publishing.py`
- Modify: `backend/app/models.py`
- Test: `backend/tests/test_c16_release_schema.py`

**Interfaces:**
- `Release` exposes `name`, `description`, `game_design_revision_id`, `gamespec_revision_id`, `artifact_path`, and `artifact_checksum`.
- `ResourceExtractionBatch` exposes `release_id`, `status`, `candidate_count`, and error metadata.

- [ ] Write schema and migration tests first. Assert the new columns and unique release batch table after `alembic upgrade head`.
- [ ] Run `backend/.venv/bin/pytest backend/tests/test_c16_release_schema.py -q` and observe the expected missing-table/column failure.
- [ ] Add the model fields and migration from `0014_c14_playable_promotion`; make downgrade remove the batch table and new columns.
- [ ] Re-run the focused schema test and then the existing C14/C20 schema tests.
- [ ] Commit: `feat: persist immutable release snapshot`

### Task 2: Add Release lifecycle service and Publish Review API

**Files:**
- Create: `backend/app/api/releases.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/services/lifecycle.py`
- Modify: `backend/app/services/checkpoint.py`
- Test: `backend/tests/test_c16_release_api.py`

**Interfaces:**
- `GET /api/v1/projects/{project_id}/publish-review` returns eligibility and target provenance.
- `GET /api/v1/projects/{project_id}/releases` and `GET /api/v1/projects/{project_id}/releases/{release_id}` return immutable release details.
- `POST /api/v1/projects/{project_id}/releases` accepts `{playable_version_id, name, description}` and returns a `ReleaseResponse`.
- `ProjectLifecycleService.publish_version(version_id, name, description)` remains the transition owner and is idempotent by playable version.

- [ ] Add failing API tests for no-current-playable review, successful publish, missing Human/verification gates, duplicate publish, and immutable snapshot after later project changes.
- [ ] Run the focused tests and confirm they fail because the routes/fields do not exist.
- [ ] Implement response models, eligibility lookup, transaction-safe publish, extraction batch creation with `status="empty"`, and C20 checkpoint tagging.
- [ ] Preserve the existing service guard that only the current Playable can publish; convert errors to the standard envelope.
- [ ] Run `backend/.venv/bin/pytest backend/tests/test_c16_release_api.py backend/tests/test_c14_api.py backend/tests/test_c20_checkpoint.py -q`.
- [ ] Commit: `feat: add persisted publish review and release api`

### Task 3: Add typed frontend Release API and remote hydration

**Files:**
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/components/workspace/releaseTypes.ts`
- Modify: `frontend/src/stores/projectStore.ts`
- Modify: `frontend/src/App.vue`
- Test: `frontend/tests/releaseApiMapping.test.mjs`

**Interfaces:**
- Client functions: `getPublishReview`, `listProjectReleases`, `getProjectRelease`, `publishProjectRelease`.
- `ProjectSession.releases` is hydrated from backend Release records for backend projects.
- `resourcePendingCount` is zero when the backend extraction batch is empty.

- [ ] Write mapping tests for snake_case API Release → `ReleaseRecord`, empty batch count, and duplicate-safe list hydration.
- [ ] Run the Node tests and observe missing exports/mapping failures.
- [ ] Add typed API interfaces and store hydration; do not remove demo fixture code used only by `?screen=publish`.
- [ ] Load releases during `hydrateProjectSession`/`openWorkspace` and preserve remote errors without replacing a known release with fixture data.
- [ ] Run `node --test frontend/tests/releaseApiMapping.test.mjs` and `cd frontend && npx vue-tsc -b`.
- [ ] Commit: `feat: hydrate remote releases in workspace`

### Task 4: Replace local Publish action for remote projects

**Files:**
- Modify: `frontend/src/screens/K02ProjectWorkspace.vue`
- Modify: `frontend/src/components/workspace/ReleaseReviewModal.vue`
- Modify: `frontend/src/components/workspace/ReleaseDetailDrawer.vue`
- Modify: `frontend/src/components/workspace/ResourceExtractionBridge.vue`
- Test: `frontend/tests/releaseWorkflow.test.mjs`

**Interfaces:**
- Remote project Publish Review displays backend eligibility/source and uses `publishProjectRelease`.
- Local demo screens retain deterministic fixture behavior behind explicit `?screen=publish`.
- Empty resource batch renders “这次发布没有新的待确认资源” and never a fake count.

- [ ] Add failing workflow tests for remote publish call, API error state, refresh-preserved Release detail and empty batch copy.
- [ ] Run the tests before implementation.
- [ ] Add the minimal UI/store action bridge; keep draft text edits local until explicit Publish.
- [ ] Ensure closing/reopening the modal does not create a Release and retry reuses the same target.
- [ ] Run focused frontend tests and `cd frontend && npx vue-tsc -b && npx vite build`.
- [ ] Commit: `feat: connect workspace publish gate to api`

### Task 5: End-to-end verification and C16 evidence

**Files:**
- Create: `backend/tests/test_c16_release_e2e.py`
- Create: `docs/development/C16_RELEASE_PUBLISHING.md`
- Modify: `docs/development/V1_FULL_SCOPE_REBASELINE_2026-08-20.md`

- [ ] Run the full backend test suite and frontend build.
- [ ] Start the backend/frontend against a clean database and manually exercise Playable → Publish Review → Publish → Release detail → refresh.
- [ ] Verify repeated Publish returns the same Release id and old Release source remains unchanged after a later Playable fixture.
- [ ] Record commands, migration head, API response shapes and any remaining C17 boundary in the evidence doc.
- [ ] Commit: `docs: record c16 release publishing verification`
