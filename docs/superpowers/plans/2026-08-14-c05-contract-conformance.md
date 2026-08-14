# C05 Contract Conformance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist immutable GDD revisions and readiness, preserve independent Human Confirm gates, and record the confirmed GDD source for each CreatorGameSpec revision.

**Architecture:** Keep the existing `GameDesign` row as a Project aggregate and add `GameDesignRevision` history. Design saves create draft revisions; confirmation changes revision status and aggregate pointers atomically. `GameSpecRevision` stores relational provenance to the confirmed GDD without adding workflow state to CreatorGameSpec. Existing API routes remain stable and gain metadata fields.

**Tech Stack:** Python 3.11, FastAPI, Pydantic, SQLAlchemy, Alembic, SQLite, pytest, Vue 3 + Vite for regression build.

## Global Constraints

- FastAPI remains the only owner of Confirm GDD and Confirm GameSpec.
- Confirmed GDD and GameSpec content is immutable; edits create new drafts/revisions.
- CreatorGameSpec remains provider-neutral and contains no provider commands, paths, ids or UI workflow state.
- Do not implement Build, OpenGame, Candidate verification, resources, Promote, Publish or frontend business-state migration.
- No Pinia, Vue Router, workflow engine, queue, worker or runtime dependency.

### Task 1: Add failing contract and migration tests

**Files:**
- Create: `backend/tests/test_c05_design_revision_contract.py`
- Modify: `backend/tests/test_c05_design_api.py`
- Modify: `backend/tests/test_c05_gamespec_api.py`
- Modify: `backend/tests/test_migrations.py`

- [ ] Write tests for readiness `not_ready/ready/blocked`, immutable confirmed content, source GDD revision and backfill.
- [ ] Run focused tests and confirm they fail because the model fields/endpoints do not exist.

### Task 2: Implement persistence and schema

**Files:**
- Modify: `backend/app/models.py`
- Modify: `backend/app/contracts/design.py`
- Modify: `backend/migrations/versions/0007_c05_design_revisions.py`

- [ ] Add revision table, aggregate pointers and GameSpec source pointer.
- [ ] Add the migration/backfill and verify it is repeatable on empty and existing databases.
- [ ] Add strict readiness DTOs with legacy payload defaulting to `not_ready`.
- [ ] Run the focused tests and confirm they pass.

### Task 3: Implement lifecycle invariants

**Files:**
- Modify: `backend/app/services/lifecycle.py`
- Modify: `backend/app/api/design.py`
- Modify: `backend/app/errors.py` only if a new error code is required

- [ ] Make design save create a new draft revision without mutating confirmed JSON.
- [ ] Make Confirm GDD validate current revision, readiness and Project ownership atomically.
- [ ] Capture confirmed GDD provenance on GameSpec drafts and block GameSpec confirmation until the design gate is confirmed.
- [ ] Run the focused API/service tests and verify error envelopes.

### Task 4: Regression and handoff

**Files:**
- Modify: `openspec/changes/c05-contract-conformance/tasks.md`
- Create: `docs/superpowers/verification/2026-08-14-c05-contract-conformance.md`

- [ ] Run all backend tests, frontend `vue-tsc -b` and `vite build`, OpenSpec strict validation and `git diff --check`.
- [ ] Verify no Build/OpenGame/Candidate/Resource/Vue business files changed.
- [ ] Record the test commands, results, migration head and remaining reviewer gate.
