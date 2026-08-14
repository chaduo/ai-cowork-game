# Change: c12-verification-conformance

## 1. Metadata

**Change ID:** C12-CORRECTIVE
**Owner:** zhao
**Reviewer:** zhang（Required Review）
**Priority:** P0
**Depends On:** C11 build context; C08-C10 runtime evidence
**Status:** Backlog

## 2. Goal

把 Candidate 验证升级为平台拥有的真实 browser evidence gate，使用 `PASSED`、`PARTIAL_FAILURE`、`CRITICAL_FAILURE` 和 `INVALID`，并限制自动修复最多三轮。

## 3. In Scope

- TestReport and TestEvidence verdict/severity schema.
- Build Check, Browser Smoke and Core Gameplay Acceptance evidence.
- Standard Phaser `window.__GAME_TEST__` hook validation.
- Reject missing, contradictory, runtime-only PASS and invalid artifact evidence.
- Repair ancestry and hard maximum of three attempts.
- Keep failed/partial candidates away from current Playable.

## 4. Out of Scope

- Human Play Review/Promote API.
- OpenGame raw logs or adapter parsing.
- Workspace UI.

## 5. Acceptance

### AC1 — Runtime cannot self-certify

**Given** runtime reports PASS without platform browser evidence
**When** the candidate is tested
**Then** the platform stores evidence as invalid and the Candidate is not ready.

### AC2 — Severity is explicit

**Given** a candidate has a recoverable failed check
**When** the platform evaluates it
**Then** it records `PARTIAL_FAILURE`; a critical or missing check records `CRITICAL_FAILURE` or `INVALID` and never opens Promote.

### AC3 — Repair limit

**Given** three repair attempts already exist
**When** another automatic repair is requested
**Then** it is rejected, and all prior candidates and evidence remain immutable.
