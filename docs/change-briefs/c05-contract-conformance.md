# Change: c05-contract-conformance

## 1. Metadata

**Change ID:** C05-CORRECTIVE
**Owner:** zhao
**Reviewer:** zhang（Required Review）
**Priority:** P0
**Depends On:** C02, C03 foundations; C00 audit
**Status:** Backlog

## 2. Goal

让 Game Design 的草稿、clarification、Design Readiness、确认 GDD revision 和 CreatorGameSpec revision 都可恢复、不可原地覆盖，并且只有独立 Human Confirm 后才能 Build。

## 3. In Scope

- GDD draft/revision persistence and immutable confirmed revision.
- Clarification/choice/input and unresolved decision persistence.
- Design Readiness result and blocking reasons.
- CreatorGameSpec validation, revision and mapping contract updates.
- Contract tests for refresh, invalid schema, duplicate confirm and new-draft-from-confirmed.

## 4. Out of Scope

- OpenGame prompt/CLI/Executor/Adapter.
- Build execution, Candidate verification and Promote.
- Resource workflow metadata in CreatorGameSpec.
- Vue visual redesign.

## 5. Acceptance

### AC1 — Confirmed GDD is immutable

**Given** a confirmed GDD revision 1
**When** the user edits design content
**Then** the API creates a new draft/revision and revision 1 remains unchanged.

### AC2 — Readiness survives refresh

**Given** unresolved clarification or design decision
**When** the user refreshes and resumes
**Then** the same pending decision and readiness blockers are returned; confirmation is rejected until resolved.

### AC3 — Build gate

**Given** a missing or invalid CreatorGameSpec
**When** a Build is requested
**Then** the API rejects it without creating an active Build.
