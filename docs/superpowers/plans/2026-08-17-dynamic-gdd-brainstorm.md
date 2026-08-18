# Dynamic GDD Brainstorming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the real-project fixed kickoff questionnaire with a provider-neutral, persisted Game Design Brainstorm loop.

**Architecture:** FastAPI owns a strict `GameDesignPlanner` boundary and the `/design/brainstorm` mutation. Production uses an OpenAI-compatible HTTP planner with backend-only credentials; tests inject a deterministic planner. Vue renders server-provided questions and keeps the existing Confirm GDD gate.

**Tech Stack:** FastAPI, Pydantic, httpx, SQLAlchemy/Alembic, Vue 3, TypeScript, Node test runner.

## Global Constraints

- No Pinia, Vue Router, workflow engine, queue, worker, or new runtime dependency.
- FastAPI remains the only owner of Confirm GDD, Project stage, and Git checkpoint mutations.
- Real Projects never silently fall back to the old fixed kickoff fixtures.
- CreatorGameDesignDraft contains design content and clarification data only; no provider credentials or UI workflow state.
- Every implementation task runs `cd frontend && npx vue-tsc -b && npx vite build` plus focused backend tests before commit.

---

### Task 1: Brainstorm contracts, provenance, and planner boundary

**Files:**
- Create: `backend/app/contracts/design_brainstorm.py`
- Create: `backend/app/agents/game_design_planner.py`
- Modify: `backend/app/contracts/design.py`
- Test: `backend/tests/test_game_design_brainstorm_contract.py`

**Interfaces:**
- `BrainstormInput(action, question_id, answer_id, answer)`
- `BrainstormQuestion(id, prompt, choices)`
- `BrainstormTurn(draft, next_question)`
- `GameDesignPlanner.plan_turn(project_id, draft, user_input)`

- [ ] Write failing contract tests for current-question persistence, choice bounds, provenance, finite gap categories, and rejecting malformed planner output.
- [ ] Run `backend/.venv/bin/pytest backend/tests/test_game_design_brainstorm_contract.py -q` and confirm the new imports/contracts fail.
- [ ] Add strict Pydantic contracts and the planner protocol; extend `ClarificationState` with `current_question`, a six-turn budget, and deterministic readiness fields without adding provider state to the draft.
- [ ] Run the focused contract test and the frontend build.
- [ ] Commit `feat: add game design brainstorm contracts`.

### Task 1.5: Deterministic draft reducer and readiness gate

**Files:**
- Create: `backend/app/services/game_design_brainstorm.py`
- Modify: `backend/app/contracts/design.py`
- Test: `backend/tests/test_game_design_brainstorm_service.py`

**Interfaces:**
- `apply_brainstorm_input(draft, input, turn) -> CreatorGameDesignDraft`
- `evaluate_first_playable_readiness(draft) -> DesignReadiness`
- `select_blocking_gap(draft) -> str | None`

- [ ] Write failing tests showing user answers become `user_confirmed`, inferred values never satisfy a required field, the six-turn budget stops questioning, and first-playable readiness is independent from full-GDD completeness.
- [ ] Run the focused service tests and confirm they fail for the missing reducer/gate.
- [ ] Implement the finite gap order, answer reducer, provenance-safe superseding decisions, no-progress stop rule, and deterministic readiness projection.
- [ ] Run the focused service tests and the frontend build.
- [ ] Commit `feat: add deterministic brainstorm reducer and readiness gate`.

### Task 2: OpenAI-compatible planner and test double

**Files:**
- Create: `backend/app/agents/openai_game_design_planner.py`
- Create: `backend/app/agents/fake_game_design_planner.py`
- Modify: `backend/app/config.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_openai_game_design_planner.py`

**Interfaces:**
- `OpenAICompatibleGameDesignPlanner.plan_turn(...)` calls `${base_url}/chat/completions` and returns validated `BrainstormTurn`.
- Missing credentials/provider failures raise structured planner exceptions; they do not return a fake turn.

- [ ] Write failing tests for JSON response parsing, fenced JSON, malformed output, missing credentials, and provider HTTP errors using `httpx.MockTransport`.
- [ ] Run the focused tests and confirm they fail before implementation.
- [ ] Implement timeout-bounded HTTP calls, secret-free diagnostics, JSON extraction, and a small injected fake planner for tests.
- [ ] Wire `GAME_DESIGN_PROVIDER`, model, base URL, API key and timeout through `Settings` and `create_app`.
- [ ] Run planner tests, backend type/import checks, and the frontend build.
- [ ] Commit `feat: add provider-neutral game design planner`.

### Task 3: Persisted brainstorm API

**Files:**
- Modify: `backend/app/api/design.py`
- Modify: `backend/app/services/lifecycle.py`
- Modify: `backend/app/contracts/design.py`
- Modify: `backend/app/main.py` if dependency wiring needs adjustment
- Modify: `frontend/src/api/client.ts`
- Test: `backend/tests/test_c05_brainstorm_api.py`

- [ ] Write failing API tests for start, answer, free-text, refresh recovery, provider error, and Confirm GDD blocking/acceptance.
- [ ] Run the focused API tests and confirm failures are caused by the missing endpoint/state.
- [ ] Implement `POST /api/v1/projects/{project_id}/design/brainstorm`; load latest draft, call planner, save a new revision, and return the next question.
- [ ] Add `next_question` to `DesignResponse` from the persisted `clarification.current_question`.
- [ ] Preserve existing `/design` and `/design/confirm` behavior and C20 checkpoint calls.
- [ ] Run the focused API tests, the existing C05 suite, and frontend build.
- [ ] Commit `feat: persist game design brainstorm turns`.

### Task 4: Dynamic kickoff UI

**Files:**
- Modify: `frontend/src/components/kickoff/kickoffTypes.ts`
- Modify: `frontend/src/components/kickoff/CreativeKickoffModal.vue`
- Modify: `frontend/src/screens/K01CreateProject.vue`
- Modify: `frontend/src/api/client.ts` if response types need refinement
- Test: `frontend/tests/gameDesignBrainstorm.test.mjs`

- [ ] Write failing pure behavior tests for rendering/restoring a server question and routing answer/free-text payloads.
- [ ] Run the tests and confirm the new dynamic helper behavior is absent.
- [ ] Add `projectId`-aware server-turn handling, restore persisted questions, keep fixture mode only for offline demo sessions, and show provider errors without advancing.
- [ ] Keep Confirm Design calling the existing API only after readiness is ready.
- [ ] Run frontend tests, `npx vue-tsc -b`, and `npx vite build`.
- [ ] Commit `feat: connect kickoff to dynamic brainstorm`.

### Task 5: End-to-end acceptance and documentation

**Files:**
- Modify: `docs/superpowers/verification/2026-08-17-dynamic-gdd-brainstorming.md`
- Test: `backend/tests/test_c05_design_api.py`, `backend/tests/test_c05_design_revision_contract.py`, frontend tests

- [ ] Run focused and full backend suites; record any environment skips.
- [ ] Run frontend tests and production build.
- [ ] Manually verify two different Ideas, free-text response, refresh/resume, blocked confirm, successful Confirm GDD, and no Build before GameSpec confirmation.
- [ ] Record API payload/state evidence and provider configuration requirements.
- [ ] Commit `docs: verify dynamic game design brainstorming`.
