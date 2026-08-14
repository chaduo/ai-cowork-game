# C12 Candidate Test Gate Design

## Goal

为 C11 产生的 BuildCandidate 建立平台校验的 TestReport/evidence 门，只有证据完整、无矛盾且通过的 Candidate 才进入 `ready`，并保留失败与 repair ancestry。

## Scope Boundary

- C12 负责 artifact 可测试性、浏览器/console/核心玩法证据的 schema、持久化和平台判定。
- 第一版使用 provider-neutral `CandidateTestRunner` 与 deterministic `FakeCandidateTestRunner`，不引入 Playwright、OpenGame subprocess 或新的 runtime dependency。
- C11 负责 Build/retry 并产生新的 Candidate；C12 负责将新 Candidate 关联到旧失败 Candidate 的 repair ancestry。
- C12 不创建 PlayableVersion、Release，不更新 `Project.current_playable_version_id`，不提供 Workspace UI。

## Data Model

### BuildCandidate additions

- `test_gate_status`: `untested | failed | invalid | ready`
- `parent_candidate_id`: nullable self-reference for repair ancestry
- `attempt`: integer, starts at 1 and increases from the parent candidate

The existing artifact/build status remains intact for C11/C02 compatibility. A failed test candidate is never a playable version and can never be treated as ready.

### TestReport

One immutable report belongs to one Candidate attempt and stores both the runtime claim and the platform verdict. Repeating the test request for the same Candidate returns the existing report instead of creating a second verdict:

- `id`, `candidate_id`, `runtime_verdict`, `platform_verdict`
- `status`: `pass | fail | invalid`
- `summary`, `diagnostics_json`, `created_at`

### TestEvidence

Evidence rows are immutable once a report is stored:

- `id`, `test_report_id`, `kind`, `status`
- `expected`, `observed`, `artifact_ref`, `details_json`, `created_at`

Required evidence kinds for a pass are `browser_started`, `console`, `core_input`, `gameplay`, and `completion`.

## Platform Validation Rules

The platform, not the runtime, computes the authoritative verdict:

1. Candidate must have a successful build status and a non-empty artifact path.
2. Every required evidence kind must be present exactly once and have `status=passed`.
3. Evidence must include an artifact reference and meaningful observed data.
4. A runtime `pass` without complete evidence becomes `invalid`, not `ready`.
5. Any failed evidence becomes `fail`; contradictory runtime/evidence claims become `invalid`.
6. Only `platform_verdict=pass` sets `candidate.test_gate_status=ready`.
7. Any non-pass result leaves `Project.current_playable_version_id` unchanged.

## Service and API

`CandidateTestService` consumes a `CandidateTestRunner`, stores the normalized report/evidence, and applies the gate atomically. The first API surface is:

- `POST /api/v1/candidates/{candidate_id}/test`
- `GET /api/v1/candidates/{candidate_id}/test-report`
- `POST /api/v1/candidates/{candidate_id}/repair-link`

The repair link accepts a newly created, still-untested Candidate from a C11 retry, verifies it belongs to the same Project and that the parent report failed or is invalid, then assigns `parent_candidate_id` and the next attempt number. A Candidate can be linked only once; it never overwrites the parent.

## Test Strategy

- Service tests cover pass, missing evidence, contradictory evidence, runtime-only PASS, build failure, artifact missing, current-playable immutability, and repair ancestry.
- API tests cover report persistence, candidate gate state, error envelopes, and idempotent report retrieval.
- Existing C01-C11 backend tests and frontend build remain regression gates.
