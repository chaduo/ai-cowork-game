# Change: c11-build-context-conformance

## 1. Metadata

**Change ID:** C11-CORRECTIVE
**Owner:** zhao
**Reviewer:** zhang（Required Review）
**Priority:** P0
**Depends On:** C05, C06, C07 corrective contracts
**Status:** Implemented on `codex/c11-build-job-orchestration`

## 2. Goal

把每次 Build 使用的 confirmed GameSpec、baseline Playable、affected scope、accepted resources、implementation dependencies 和 overrides 持久化为不可变 Build Context，并将其传给 GameAgent。

## 3. In Scope

- Build Context schema, persistence and provenance.
- Snapshot/hash of input revisions before provider invocation.
- Retry/continuation rules that preserve the original context.
- Candidate linkage proving which context produced the artifact.
- Tests for refresh, restart, retry and cross-project isolation.

## 4. Out of Scope

- OpenGame subprocess and log parser.
- Browser verification verdicts.
- Promote, Publish or Resource Review UI.

## 5. Acceptance

### AC1 — Immutable input

**Given** a confirmed GameSpec and baseline Playable
**When** a Build starts
**Then** changing later project state does not change the Build Context or Candidate provenance.

### AC2 — Candidate-only success

**Given** a successful provider result
**When** the Build finishes
**Then** exactly one Candidate references the stored context and current Playable remains unchanged.

## Implementation Evidence

- Migration `0009_c11_build_context` adds one immutable `BuildContext` per Build and links `BuildCandidate.build_context_id`.
- Canonical CreatorGameSpec/RuntimeBuildSpec snapshots and SHA-256 hashes are captured before the first provider call.
- A Build request carries affected scope, accepted resource references, implementation dependencies and relevant overrides; duplicate requests cannot replace them.
- Provider requests are reconstructed from the stored context after refresh/restart, and retry creates a copied context without mutating the parent.
- C11 focused tests: `17 passed`; full backend: `118 passed, 1 warning`; frontend build passed.
