# C02 Project Lifecycle Domain Implementation Plan

> **For agentic workers:** Execute task-by-task with TDD and verify each task before moving on.

**Goal:** Persist the first project lifecycle entities and enforce safe domain transitions for design, GameSpec, Build, Candidate, PlayableVersion, and Release.

**Architecture:** SQLAlchemy ORM models map the C02 tables. Focused repositories perform persistence queries, while `ProjectLifecycleService` owns transactions and cross-entity state transitions. Project stage is derived from persisted state and never stored.

**Tech Stack:** Python 3.11+, FastAPI C01 foundation, SQLAlchemy 2.x ORM, Alembic, SQLite, pytest.

## Global Constraints

- No Vue, OpenGame, build execution, SSE, queue, worker, resource extraction, or TestReport table.
- BuildCandidate never updates the current playable pointer.
- Failed, cancelled, and orphaned builds never create PlayableVersion or Release.
- Every production behavior starts with a failing test.

### Task 1: Models and migration

- [ ] Add failing schema test for all C02 tables and constraints.
- [ ] Run the focused test and observe missing tables.
- [ ] Add ORM models and Alembic revision `0002_project_lifecycle_domain`.
- [ ] Run migration/schema tests and C01 regression tests.
- [ ] Commit `feat(c02): add project lifecycle schema`.

### Task 2: Design and GameSpec transitions

- [ ] Add failing tests for Project creation, design confirmation, immutable revisions, and derived early stages.
- [ ] Implement repositories and service methods.
- [ ] Run focused and full backend tests.
- [ ] Commit `feat(c02): add design and gamespec lifecycle`.

### Task 3: Build and Candidate guard

- [ ] Add failing tests for confirmed-spec precondition, active-build guard, success/failure/cancel, retry, and current playable safety.
- [ ] Implement transactional build methods and candidate persistence.
- [ ] Run focused and full backend tests.
- [ ] Commit `feat(c02): add build candidate lifecycle`.

### Task 4: Promote, Publish, and recovery

- [ ] Add failing tests for explicit PASS promotion, immutable versions, publish, orphan recovery, idempotency, and stage derivation.
- [ ] Implement service methods and recovery.
- [ ] Run focused and full backend tests.
- [ ] Commit `feat(c02): enforce promotion publish and recovery gates`.

### Task 5: Verification

- [ ] Run backend tests and migration twice against a temporary database.
- [ ] Run frontend typecheck/build.
- [ ] Check no out-of-scope files or tables were added.
- [ ] Write verification evidence and commit it.
