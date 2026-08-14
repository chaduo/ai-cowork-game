# C05 Contract Conformance Verification

**Date:** 2026-08-14
**Branch:** `feature/c05-contract-conformance`
**Base:** `origin/main` at `649bc37`
**Migration head:** `0007_c05_design_revisions`

## Scope verified

- `GameDesignRevision` stores immutable GDD snapshots with readiness metadata.
- `GameDesign.current_revision_id` and `confirmed_revision_id` distinguish the editable draft from the Human Confirmed revision.
- Saving after confirmation creates a new draft revision and preserves the confirmed snapshot/pointer.
- Confirm GDD rejects `not_ready`, blockers, and unresolved decisions through the existing API error envelope.
- `GameSpecRevision.source_design_revision_id` records the confirmed GDD revision used to create the GameSpec.
- GameSpec confirmation remains a separate Human Gate and requires confirmed Game Design.
- Legacy rows are backfilled without changing their original design JSON; confirmed rows become ready revision 1, unconfirmed rows become not-ready revision 1.

## Verification commands

```text
VENV=/Users/zhaozhuo/workspace/explore/ai-cowork-game/.worktrees/platform-backend-foundation/backend/.venv/bin
"$VENV/pytest" backend/tests -q
# 102 passed, 1 warning

npm --prefix frontend ci
npm --prefix frontend run build
# vue-tsc and Vite build passed

openspec validate c05-contract-conformance --strict
# Change 'c05-contract-conformance' is valid

git diff --check
# passed
```

The focused C05 red phase produced the expected failures before implementation; the green phase passed the revision, migration, API, service, and build-gate regressions. Migration tests cover empty databases and upgrade from `0006_candidate_test_gate`.

## Scope audit

Changed files are limited to the design/GameSpec contract, lifecycle service/API, migration, focused regression tests, and frontend API type declarations. No Build/OpenGame execution, Candidate verification, Resource workflow, or Vue business-state implementation was added.

## Reviewer gate

A human reviewer should inspect the migration backfill policy and confirm that the client can display readiness blockers before allowing Confirm GDD in the production flow. C05 does not add UI presentation for blockers; it only makes the contract and server gate explicit.
