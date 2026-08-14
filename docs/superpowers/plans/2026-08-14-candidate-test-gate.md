# C12 Candidate Test Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist platform-validated TestReport/evidence for C11 BuildCandidates and mark only complete, non-contradictory passes as ready without changing the current playable pointer.

**Architecture:** Add immutable `TestReport` and `TestEvidence` records plus test-gate and repair fields on `BuildCandidate`. A `CandidateTestService` consumes a provider-neutral `CandidateTestRunner`; the deterministic fake runner supplies fixtures while the service owns evidence validation and the authoritative verdict. A small candidates API exposes test, report retrieval, and repair-link operations.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, pytest, existing SQLite database and C11 service patterns.

## Global Constraints

- Do not add Playwright, browser drivers, OpenGame subprocesses, queues, workers, or runtime dependencies.
- Do not update `Project.current_playable_version_id`, create `PlayableVersion`, publish `Release`, or add Workspace UI.
- Runtime verdicts are claims only; platform evidence validation is authoritative.
- Failed/invalid Candidate and TestReport records are immutable history; repairs create a new Candidate attempt and preserve the parent.
- Existing C01-C11 tests and frontend build must remain green.

---

### Task 1: Persist candidate gate and TestReport schema

**Files:**
- Modify: `backend/app/models.py`
- Create: `backend/migrations/versions/0006_candidate_test_gate.py`
- Test: `backend/tests/test_c12_schema.py`

**Interfaces:**
- `BuildCandidate.test_gate_status`: `untested | failed | invalid | ready`.
- `BuildCandidate.parent_candidate_id`: nullable self-FK.
- `BuildCandidate.attempt`: integer default 1.
- `TestReport` has one unique `candidate_id`, `runtime_verdict`, `platform_verdict`, `status`, `summary`, `diagnostics_json`, timestamps.
- `TestEvidence` belongs to `TestReport` and stores `kind`, `status` (`passed | failed | missing`), expected/observed text, artifact reference, and details JSON.

- [ ] **Step 1: Write failing schema tests**

Add tests that upgrade a fresh database to head and assert the new tables/columns exist. Insert a candidate with `attempt=2` and a parent candidate, then insert one report and five evidence rows and reload them.

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
$VENV/pytest backend/tests/test_c12_schema.py -q
```

Expected: collection or assertion failure because `TestReport`, `TestEvidence`, and the new Candidate columns do not exist.

- [ ] **Step 3: Implement the model and migration**

Use SQLAlchemy typed mappings and a repeatable Alembic migration from `0005_build_job_orchestration`. Add indexes/unique constraints for candidate/report ownership and report evidence ordering. Use nullable `parent_candidate_id` with a self-reference and do not alter existing BuildCandidate `status` semantics.

- [ ] **Step 4: Run schema tests to verify they pass**

Run:

```bash
$VENV/pytest backend/tests/test_c12_schema.py -q
```

Expected: all C12 schema tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models.py backend/migrations/versions/0006_candidate_test_gate.py backend/tests/test_c12_schema.py
git commit -m "feat: persist candidate test gate records"
```

### Task 2: Define runner contract and platform evidence validation

**Files:**
- Create: `backend/app/contracts/test_report.py`
- Create: `backend/app/agents/candidate_test_runner.py`
- Create: `backend/app/agents/fake_candidate_test_runner.py`
- Create: `backend/app/services/candidate_tests.py`
- Test: `backend/tests/test_c12_candidate_test_gate.py`

**Interfaces:**
- `CandidateTestEvidence(kind, status, expected, observed, artifact_ref, details)`.
- `RuntimeTestResult(verdict, evidence, diagnostics)` where verdict is `pass | fail | unknown`.
- `CandidateTestRunner.run(candidate) -> RuntimeTestResult`.
- `CandidateTestService(session, runner)` and `test_candidate(candidate_id) -> TestReport`.
- Required evidence kinds are `browser_started`, `console`, `core_input`, `gameplay`, and `completion`.

- [ ] **Step 1: Write failing service tests**

Cover these behaviors separately: complete evidence produces `platform_verdict=pass` and Candidate `test_gate_status=ready`; runtime PASS with missing evidence produces `invalid`; any failed evidence produces `fail`; contradictory runtime/evidence claims produce `invalid`; build failure or missing artifact cannot become ready; repeated test returns the existing immutable report; current playable remains unchanged.

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
$VENV/pytest backend/tests/test_c12_candidate_test_gate.py -q
```

Expected: import or assertion failures because the runner contract and service do not exist.

- [ ] **Step 3: Implement the provider-neutral contract and fake fixtures**

Keep the runner unaware of platform gate state. Make `FakeCandidateTestRunner` deterministic and injectable with named fixtures: `pass`, `missing_evidence`, `contradictory`, `console_failure`, `completion_failure`, and `runtime_only_pass`.

- [ ] **Step 4: Implement the service validator**

Load the Candidate and its Build, reject non-success or empty-artifact candidates into an immutable invalid report, normalize runner evidence, enforce exactly one row per required kind, require artifact references and observed values, then compute the platform verdict. Persist report/evidence and Candidate gate state in one transaction. Never call lifecycle promotion methods.

- [ ] **Step 5: Run service tests to verify they pass**

Run:

```bash
$VENV/pytest backend/tests/test_c12_candidate_test_gate.py -q
```

Expected: all platform-validation cases pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/contracts/test_report.py backend/app/agents/candidate_test_runner.py backend/app/agents/fake_candidate_test_runner.py backend/app/services/candidate_tests.py backend/tests/test_c12_candidate_test_gate.py
git commit -m "feat: validate candidate test evidence"
```

### Task 3: Add repair ancestry operation

**Files:**
- Modify: `backend/app/services/candidate_tests.py`
- Test: `backend/tests/test_c12_candidate_test_gate.py`

**Interfaces:**
- `CandidateTestService.link_repair_candidate(parent_candidate_id, replacement_candidate_id) -> BuildCandidate`.

- [ ] **Step 1: Write failing repair tests**

Assert a failed/invalid parent can link one same-project, untested replacement; replacement receives `parent_candidate_id` and `attempt=parent.attempt+1`; parent status/report stays unchanged. Assert successful, cross-project, already-tested, and already-linked parents are rejected.

- [ ] **Step 2: Run the focused tests to verify they fail**

```bash
$VENV/pytest backend/tests/test_c12_candidate_test_gate.py -k repair -q
```

Expected: failure because the service method is not implemented.

- [ ] **Step 3: Implement repair linking transactionally**

Validate both candidates, same project, parent report status `fail` or `invalid`, replacement gate status `untested`, and no existing parent link. Update only the replacement ancestry fields and leave the failed record immutable.

- [ ] **Step 4: Run repair tests and the full C12 service suite**

```bash
$VENV/pytest backend/tests/test_c12_candidate_test_gate.py -q
```

Expected: all service and repair tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/candidate_tests.py backend/tests/test_c12_candidate_test_gate.py
git commit -m "feat: preserve candidate repair ancestry"
```

### Task 4: Expose candidate testing APIs

**Files:**
- Create: `backend/app/api/candidates.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_c12_candidate_api.py`

**Interfaces:**
- `POST /api/v1/candidates/{candidate_id}/test`
- `GET /api/v1/candidates/{candidate_id}/test-report`
- `POST /api/v1/candidates/{candidate_id}/repair-link` with `replacement_candidate_id`.

- [ ] **Step 1: Write failing API tests**

Test pass response, invalid/missing evidence response, report retrieval idempotency, unknown candidate error envelope, and repair-link response. Assert API responses expose `test_gate_status`, platform verdict, evidence, and attempt ancestry without exposing a Promote action.

- [ ] **Step 2: Run API tests to verify they fail**

```bash
$VENV/pytest backend/tests/test_c12_candidate_api.py -q
```

Expected: 404/import failures because the router is not registered.

- [ ] **Step 3: Implement the router**

Use the existing `ApiError` envelope and session patterns. Inject the app-level deterministic fake runner, return the existing report on repeated test calls, commit successful transactions, and map domain validation failures to 404/409 responses.

- [ ] **Step 4: Register the router and run API tests**

```bash
$VENV/pytest backend/tests/test_c12_candidate_api.py -q
```

Expected: all API tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/candidates.py backend/app/main.py backend/tests/test_c12_candidate_api.py
git commit -m "feat: expose candidate test gate api"
```

### Task 5: Regression verification and documentation

**Files:**
- Modify: `docs/development/V1_CHANGE_CATALOG.md`
- Create: `docs/superpowers/verification/2026-08-14-candidate-test-gate.md`

- [ ] **Step 1: Run the complete backend suite**

```bash
$VENV/pytest backend/tests -q
```

Expected: all pre-existing C01-C11 tests plus C12 tests pass.

- [ ] **Step 2: Run the frontend build**

```bash
npm --prefix frontend run build
```

Expected: `vue-tsc -b` and Vite build exit successfully.

- [ ] **Step 3: Run migration and API smoke checks**

Upgrade a temporary SQLite database to head, call `/healthz`, test one passing Candidate and one invalid Candidate through the API, and verify the Project current playable pointer is unchanged.

- [ ] **Step 4: Write verification evidence and update C12 Catalog evidence**

Record test counts, migration revision, API cases, and the explicit C12 boundary that no Promote/Playable/Release/UI behavior was added.

- [ ] **Step 5: Commit**

```bash
git add docs/development/V1_CHANGE_CATALOG.md docs/superpowers/verification/2026-08-14-candidate-test-gate.md
git commit -m "docs: record candidate test gate verification"
```
