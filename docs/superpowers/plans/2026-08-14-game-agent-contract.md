# Game Agent Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze and test a provider-neutral GameAgent boundary for BuildService.

**Architecture:** Pydantic models in `backend/app/contracts/game_agent.py` define serialized request, result,
error, artifact, handle, and RunEvent values. `backend/app/agents/game_agent.py` defines the async protocol
and `backend/app/agents/fake_game_agent.py` provides deterministic behavior. A reusable pytest suite proves
the contract without coupling it to any provider or lifecycle repository.

**Tech Stack:** Python 3.11, Pydantic 2, pytest, `typing.Protocol`, async iterators.

## Global Constraints

- BuildService must not know OpenGame commands, logs, or SDK types.
- Agent/provider output cannot Promote, Publish, or save resources.
- No new runtime dependency, database migration, API route, queue, worker, or frontend workflow.
- Fake runtime is for contract tests only and never counts as real OpenGame evidence.

---

### Task 1: Contract models

**Files:**
- Create: `backend/app/contracts/game_agent.py`
- Modify: `backend/app/contracts/__init__.py`
- Test: `backend/tests/test_c06_game_agent_contract.py`

**Interfaces:**
- Produces `GameBuildRequest`, `GameBuildResult`, `ArtifactManifestEntry`, `Diagnostic`, `ContractError`,
  `AgentRunHandle`, and `RunEvent`.
- `RunEvent` rejects lifecycle gate event kinds and invalid progress; result statuses are terminal and typed.

- [x] **Step 1: Write failing model tests** covering valid request/result/event, forbidden gate events, invalid
  progress, and unsupported status.
- [x] **Step 2: Run `pytest backend/tests/test_c06_game_agent_contract.py -q` and verify the new imports fail.**
- [x] **Step 3: Implement the minimal Pydantic models with `extra="forbid"`, length bounds, UTC timestamp,
  structured error, and artifact path fields.
- [x] **Step 4: Run the focused test and then the existing backend suite.**
- [x] **Step 5: Commit `feat: add provider-neutral game agent contracts`.**

### Task 2: Protocol and deterministic fake agent

**Files:**
- Create: `backend/app/agents/__init__.py`
- Create: `backend/app/agents/game_agent.py`
- Create: `backend/app/agents/fake_game_agent.py`
- Modify: `backend/app/contracts/__init__.py`
- Test: `backend/tests/test_c06_game_agent_contract.py`

**Interfaces:**
- `GameAgent.start(request) -> AgentRunHandle`.
- `GameAgent.stream_events(handle, after_sequence=0) -> AsyncIterator[RunEvent]`.
- `GameAgent.result(handle) -> GameBuildResult`.
- `GameAgent.cancel(handle) -> None`.
- `FakeGameAgent(outcome_by_operation: Mapping[str, GameBuildStatus] | None = None)`.

- [x] **Step 1: Add failing behavior tests for deterministic success events, terminal result, unsupported operation,
  cancellation, timeout, and invalid output.**
- [x] **Step 2: Run the focused tests and verify the fake agent/protocol imports or assertions fail.**
- [x] **Step 3: Implement the protocol and in-memory fake with stable run IDs, sequence numbers, sanitized
  diagnostics, and no lifecycle mutations.
- [x] **Step 4: Run focused and full backend tests.**
- [x] **Step 5: Commit `feat: add fake game agent contract runtime`.**

### Task 3: Shared contract suite and documentation alignment

**Files:**
- Create: `backend/tests/contract_suites/test_game_agent_contract_suite.py`
- Modify: `backend/tests/test_c06_game_agent_contract.py`
- Modify: `specs/001-game-creation-mvp/contracts/game-agent-adapter.md`

**Interfaces:**
- `assert_game_agent_contract(agent_factory)` is reusable by C10 OpenGameAdapter and future Claude/piagent
  adapters.

- [x] **Step 1: Extract shared assertions for success, event replay ordering, unsupported operation, cancellation,
  timeout, invalid output, and forbidden gate events.**
- [x] **Step 2: Run the suite against `FakeGameAgent` and verify all cases pass.**
- [x] **Step 3: Align the contract document with the implemented terminal statuses, handle lifecycle, and explicit
  C10 adapter reuse boundary without adding provider-specific implementation.
- [x] **Step 4: Run `pytest backend/tests -q`, `cd frontend && npx vue-tsc -b && npx vite build`, and `git diff --check`.**
- [x] **Step 5: Commit `docs: align game agent contract evidence`.**
