# Change: c07-run-input-conformance

## 1. Metadata

**Change ID:** C07-CORRECTIVE
**Owner:** zhao
**Reviewer:** zhang（Required Review）
**Priority:** P1
**Depends On:** C06 corrective contract
**Status:** Implemented on `codex/c06-c07-corrective`

## 2. Goal

让 RunEvent/SSE 持久化并恢复 `waiting_for_input`、phase transition 和 continuation，刷新或重连时不创建第二个 run。

## 3. In Scope

- Pending decision record and stable decision identity.
- `build.needs_input`, `build.phase_changed` and sanitized continuation events.
- REST replay and SSE reconnect from `last_sequence`.
- Terminal/non-terminal invariants and restart recovery tests.

## 4. Out of Scope

- OpenGame raw log parsing.
- Workspace UI.
- Candidate promotion or verification.

## 5. Acceptance

### AC1 — Waiting input is non-terminal

**Given** an active run emits `waiting_for_input`
**When** the user refreshes
**Then** the same run and pending decision are returned and no new run is created.

### AC2 — Replay ordering

**Given** a client reconnects with a last sequence
**When** it requests JSON replay or SSE
**Then** events are returned exactly once in increasing sequence order.

## Implementation Evidence

- Migration `0008_c07_run_input_conformance` adds `run_pending_decisions` and persists `RunEvent.decision_id`.
- `RunRepository.mark_waiting_for_input` and `continue_run` keep one stable run, enforce sequence/ownership, and make identical retries idempotent.
- `GET /api/v1/runs/{run_id}` exposes a pending decision; `POST /api/v1/runs/{run_id}/input` continues the same run.
- Waiting runs are excluded from orphan recovery; terminal cancellation closes unresolved decisions.
- JSON replay and SSE `Last-Event-ID` continue to replay only later sequence numbers.
- Verification: focused C07 tests `19 passed`; full backend suite `113 passed, 1 warning`; frontend build passed.
