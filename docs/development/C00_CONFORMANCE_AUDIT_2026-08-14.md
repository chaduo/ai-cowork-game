# C00 Conformance Audit

**Date:** 2026-08-14
**Change:** C00 `v1-contract-alignment`
**Owner:** zhao
**Required Reviewer:** zhang
**Audit status:** Self-review complete; Required Review pending

## Purpose

这份报告收口 C00 的 repository audit。它区分：

- 已合并的实现基础；
- 已满足 C00 contract 的行为；
- 只有部分满足、需要 corrective Change 的行为；
- 尚无真实实现或 evidence 的行为。

C01-C12 已经合并到当前 `main`，但“代码存在”不等于“符合最新版 V1 Design Spec”。本报告不重写已完成 Change 的历史验收，而是把差距转成独立、可审查的后续输入。

## Authority and Evidence

事实源顺序：

1. `docs/product/AI_COWORK_GAME_V1_DESIGN_SPEC.md`
2. `openspec/changes/v1-contract-alignment/`
3. `docs/development/V1_CHANGE_CATALOG.md`
4. `docs/development/V1_CONTRACT_MIGRATION_MATRIX.md`
5. merged code and tests as conformance evidence

Current repository evidence:

| Evidence | Result |
|---|---|
| `main` and `origin/main` | `6ab1b6e` (PR #6, C02-C12 foundation integration) |
| Backend regression | `96 passed, 1 warning` |
| Frontend verification | `vue-tsc -b` and `vite build` passed |
| Database migrations | `0001_foundation` through `0006_candidate_test_gate` |
| C00 OpenSpec | `12/20` tasks reported by `openspec list`; closeout/review tasks remain open |
| Legacy OpenSpec | `platform-v1-opengame-baseline` and `platform-v2-claude-agent-runtime` remain migration inputs, not authorities |

## C01-C12 Classification

| Change | Classification | Evidence | Gap / decision |
|---|---|---|---|
| C01 Backend Foundation | Foundation aligned; final acceptance evidence pending | `backend/app/config.py`, `db.py`, `errors.py`, migrations `0001`; health, migration, transaction and error tests | API client/proxy and clean-environment operational evidence still need a dedicated integration check. No corrective business Change is required before C02. |
| C02 Project Lifecycle Domain | Partial conformance | `backend/app/models.py`, `services/lifecycle.py`, C02 schema/build/promotion/recovery tests | Core Project/Build/Candidate/Playable/Release relations exist, but Git checkpoints, immutable GDD revisions and the expanded Design Spec gates are downstream contracts. Treat C02 as merged foundation, not final V1 lifecycle completion. |
| C03 Create Project Flow | Partial conformance | `api/projects.py`, idempotency migration `0003`, `test_c03_projects_api.py` | Backend creation and duplicate idempotency are covered. K01/App still hydrate a local `projectStore`; real browser refresh must prove that backend data is the only business source. |
| C04 Projects List | Partial conformance | project list API and `test_c04_projects_list.py`; App calls `listProjectRecords()` | List DTO exists, but Workspace restoration still bridges into local prototype state. Keep C04 merged; finish API-owned restoration in the later Workspace Change. |
| C05 Design/GameSpec Flow | Corrective Change required | `GameDesign` is one mutable row in `backend/app/models.py`; `GameSpecRevision` exists; C05 tests cover draft/confirm/validation | No immutable confirmed GDD revision or persisted Design Readiness/clarification decision model. CreatorGameSpec fields are useful but the review/confirm contract is incomplete. See `c05-contract-conformance`. |
| C06 Game Agent Contract | Corrective Change required | `backend/app/contracts/game_agent.py`, `gamespec.py`, C06 contract suite | Base provider-neutral request/result/event models exist, but `GameBuildRequest` lacks `affected_scope`, `resource_references` and `relevant_overrides`; `waiting_for_input`/continuation and profile capability semantics are not represented. See `c06-agent-context-conformance`. |
| C07 Run Event Observability | Corrective Change required | `repositories/runs.py`, migration `0004`, C07 replay/SSE/orphan tests | Sequence, replay, sanitization, cancel and orphan recovery exist. The contract still needs durable `waiting_for_input`, pending decision identity, `build.phase_changed` and continuation semantics. See `c07-run-input-conformance`. |
| C08 OpenGame CLI Spike | Evidence pending | Catalog C08 boundary exists; no real CLI evidence artifact is present in `main` | Must produce version, invocation, output tree, exit code, timeout/cancel and unsupported fixtures. This remains zhang-owned and independent of C00 corrective implementation. |
| C09 OpenGame Executor | Not present in merged `main` | No `OpenGameExecutor` implementation or evidence fixture in `backend/app` | Start only after C08 evidence. Keep subprocess policy outside BuildService and Project repositories. |
| C10 OpenGame Adapter | Not present in merged `main` | No OpenGame adapter implementation or parser/mapper fixture in `backend/app` | Start after C06 contract correction and C09 executor. Provider-specific types must stop at the adapter boundary. |
| C11 Build Job Orchestration | Corrective Change required | `services/builds.py`, `services/lifecycle.py`, migration `0005`, C11 FakeGameAgent tests | Stable Build/Run IDs, active-build guard, retry, cancellation and Candidate-only success exist. Build input persists GameSpec revision and baseline, but not the full immutable task-scoped context required by C00. See `c11-build-context-conformance`. |
| C12 Candidate Test Gate | Corrective Change required | `services/candidate_tests.py`, migration `0006`, C12 evidence/repair tests | Platform evidence validation and repair ancestry exist, but verdicts are still `pass/fail/invalid`, the runner is deterministic fake-only, no real browser/test hook evidence is validated, and the three-round repair limit is not enforced. See `c12-verification-conformance`. |

## Required Corrective Inputs

The following briefs are intentionally separate so each can receive an independent OpenSpec proposal, contract review, implementation and browser/evidence gate:

- `docs/change-briefs/c05-contract-conformance.md`
- `docs/change-briefs/c06-agent-context-conformance.md`
- `docs/change-briefs/c07-run-input-conformance.md`
- `docs/change-briefs/c11-build-context-conformance.md`
- `docs/change-briefs/c12-verification-conformance.md`

C08-C10 do not get absorbed into these briefs; they remain the OpenGame provider sequence from the Catalog.

## Downstream Ready Gate

The following are blocked from being called V1 Done until the corrective inputs are accepted:

- C14 Promote cannot ignore `Human Play Review`, Amendment and unresolved Drift.
- C15 Workspace cannot treat local prototype state or a timer as business truth.
- C16-C18 cannot claim immutable Release/Resource provenance while C11 context is incomplete.
- C19 cannot use FakeGameAgent, frontend fixtures or the current deterministic test runner as real E2E evidence.

## C00 Self-Review

- [x] No automatic Human Gate transition is authorized by C00.
- [x] Candidate, ResourceCandidate, PlayableVersion, Release and SavedResource remain separate.
- [x] CreatorGameSpec remains provider-neutral and excludes runtime commands, paths and UI workflow state.
- [x] P0 and P1 remain mandatory V1 scope; wave order is not scope deferral.
- [x] Legacy OpenSpec baselines are marked migration input and are not cited as implementation authority.
- [x] C01-C12 gaps are routed to named corrective Changes instead of being silently rewritten.
- [ ] zhang Required Review has been recorded.
- [ ] C00 closeout can be marked Done before the Required Review and corrective Change inputs are accepted.

## Next Gate

1. zhang reviews this report and the C06/C08 boundary.
2. Approve the five corrective briefs as OpenSpec Explore inputs.
3. Start C05 contract conformance from `origin/main`.
4. Keep C14/C15 blocked from final Done until C05-C07/C11-C12 corrections are merged and re-verified.
