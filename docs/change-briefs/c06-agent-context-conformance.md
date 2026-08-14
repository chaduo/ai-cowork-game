# Change: c06-agent-context-conformance

## 1. Metadata

**Change ID:** C06-CORRECTIVE
**Owner:** zhao
**Reviewer:** zhang（Required Review）
**Priority:** P0
**Depends On:** C00 audit, C05 contract conformance
**Status:** Implemented on `codex/c06-c07-corrective`

## 2. Goal

补齐 provider-neutral Agent Runtime contract，使 Game Build 请求携带完整 task-scoped context，并为 `waiting_for_input`、continuation 和 capability/version/error envelope 留出明确语义。

## 3. In Scope

- Add `affected_scope`, `resource_references` and `relevant_overrides` to `GameBuildRequest`.
- Define Game Design, GameSpec and Game Build profile capability/version fields without making Verification an Agent profile.
- Define standard `waiting_for_input`, timeout, cancel, invalid-output and unsupported results.
- Keep Promote, Publish and Resource Review decisions outside provider events.
- Extend FakeGameAgent and shared contract suite.

## 4. Out of Scope

- OpenGame command parsing or subprocess execution.
- Build repository/service orchestration.
- Human Gate API implementation.

## 5. Acceptance

### AC1 — Provider replacement

**Given** two providers implementing the same profile contract
**When** one provider is replaced
**Then** Project lifecycle, Human Gates and Candidate semantics do not change.

### AC2 — Context completeness

**Given** an accepted resource or implementation override
**When** a build request is created
**Then** the immutable request contains the reference and provenance, or the request is rejected.

### AC3 — Pending decision

**Given** the provider needs a user decision
**When** it returns a pending result
**Then** the platform stores a non-terminal `waiting_for_input` state without allowing Promote or Publish.

## Implementation Evidence

- `GameBuildRequest` now carries affected scope, accepted resource provenance, relevant overrides and versioned design/spec/build profiles.
- `GameBuildResult` and `RunEvent` define the non-terminal `waiting_for_input`/`decision_id` contract; provider events still reject Promote, Publish and Resource Review semantics.
- `FakeGameAgent` emits deterministic pending decisions for contract tests.
- Commits: `8513141 feat: close c06 agent context contract` and `f5c0252 feat: persist run input continuation`.
- Verification: C06 focused tests and the full backend suite pass on the corrective branch.
