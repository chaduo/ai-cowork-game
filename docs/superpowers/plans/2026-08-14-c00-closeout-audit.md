# C00 Closeout Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the C00 contract audit with evidence from the merged C01-C12 foundation, record remaining conformance gaps, and create bounded corrective Change inputs without changing product code.

**Architecture:** Treat the approved Design Spec and C00 governance artifacts as the contract authority. Compare each C01-C12 implementation against that authority, classify the result as aligned, partial, blocked, or evidence-pending, and route every gap to a focused downstream Change Brief. This audit updates planning evidence only; it does not silently rewrite completed Change history or implement business behavior.

**Tech Stack:** Markdown documentation, OpenSpec `spec-driven` artifacts, existing FastAPI/Vue evidence, pytest, Vue typecheck/Vite build.

## Global Constraints

- FastAPI remains the sole owner of persisted lifecycle mutations and Human Gates.
- CreatorGameSpec remains provider-neutral and contains no provider commands, workspace paths, resource workflow state, or UI state.
- BuildCandidate, ResourceCandidate, PlayableVersion, Release, and SavedResource remain separate concepts with direct provenance.
- C01-C12 code is audited as merged implementation evidence; completed history is not silently rewritten.
- No backend, frontend, OpenGame, Pinia, Vue Router, queue, worker, or runtime dependency changes are part of this audit.

### Task 1: Collect and classify C01-C12 evidence

**Files:**
- Read: `docs/product/AI_COWORK_GAME_V1_DESIGN_SPEC.md`
- Read: `openspec/changes/v1-contract-alignment/specs/v1-contract-governance/spec.md`
- Read: `docs/development/V1_CONTRACT_MIGRATION_MATRIX.md`
- Read: merged `backend/app/**`, `backend/tests/**`, `frontend/src/**`
- Create: `docs/development/C00_CONFORMANCE_AUDIT_2026-08-14.md`

- [ ] Record commit/worktree evidence and the latest backend/frontend verification.
- [ ] Classify C01-C12 individually as aligned, partial, blocked, or evidence-pending.
- [ ] Cite concrete files/tests for every classification and name the exact contract gap.
- [ ] Record the C00 task status discrepancy: planning artifacts are merged, but required conformance and reviewer gates remain open.

### Task 2: Create bounded corrective Change inputs

**Files:**
- Create: `docs/change-briefs/c05-contract-conformance.md`
- Create: `docs/change-briefs/c06-agent-context-conformance.md`
- Create: `docs/change-briefs/c07-run-input-conformance.md`
- Create: `docs/change-briefs/c11-build-context-conformance.md`
- Create: `docs/change-briefs/c12-verification-conformance.md`

- [ ] Give each corrective brief one owner, one reviewer, dependencies, in/out of scope, acceptance, and evidence requirements.
- [ ] Keep C08-C10 as separate provider/runtime Changes; do not pull OpenGame implementation into the corrective briefs.
- [ ] State that each corrective Change must create/update its own OpenSpec artifacts before code changes.

### Task 3: Reconcile C00 planning state and validate

**Files:**
- Modify: `openspec/changes/v1-contract-alignment/tasks.md`
- Modify: `docs/change-briefs/v1-contract-alignment.md`
- Modify: `docs/development/V1_CHANGE_CATALOG.md`
- Modify: `docs/development/V1_CONTRACT_MIGRATION_MATRIX.md`

- [ ] Mark only evidence-backed C00 planning tasks complete and leave human review/merge tasks explicitly pending.
- [ ] Update the Catalog and migration matrix to say C01-C12 are merged foundations pending conformance audit, not unmerged implementation branches.
- [ ] Link every corrective brief from the audit and record that legacy OpenSpec changes remain migration input only.
- [ ] Run `openspec validate v1-contract-alignment --strict`.
- [ ] Run backend tests and frontend typecheck/build; run `git diff --check`.
- [ ] Perform a self-review for duplicate truth sources, unbounded scope, and claims unsupported by repository evidence.
