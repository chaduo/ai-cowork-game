# Human Gate Regression Repair Design

**Date:** 2026-08-19
**Scope:** Frontend build repair and restoration of the explicit Candidate review gates

## Goal

Restore a buildable frontend while preserving the V1 rule that a successful Build produces a Candidate, not a Playable. Platform Verification, Human Play Review, and Promote remain separate transitions, with both Human Play Review and Promote requiring explicit user actions.

## Changes

1. Restore the component-local `humanReviewNotes` ref in `K02ProjectWorkspace.vue`. The existing textarea and accept/reject handlers continue to use this value when recording the Human Play Review.
2. Remove the unused `autoDeliveryStatus` prop from `BuildCoworkPanel.vue`.
3. Restore Candidate-ready messaging that says the Candidate is waiting for platform verification and Human Play Review. The build activity panel must not claim that Human Play Review or Promote happened automatically.

No backend state transition, API contract, provider behavior, or C21 behavior changes in this repair.

## State Flow

```text
Build succeeds
  -> Build Candidate
  -> Platform Verification
  -> explicit Human Play Review accept/reject
  -> explicit Promote after acceptance
  -> current Playable
```

At no point may frontend presentation imply that the last two transitions are automatic.

## Error Handling

- Review submission errors continue to render through the existing `reviewError` state.
- Promote errors continue to render through the existing `promoteError` state.
- Notes remain optional and local until the user submits an accept or reject decision.

## Verification

- Use the current failing `npm run build` result as the regression reproduction: TypeScript cannot resolve `humanReviewNotes`.
- After the repair, run all `frontend/tests/*.test.mjs` contract tests.
- Run `npm run build` and require both `vue-tsc -b` and Vite production build to succeed.
- Inspect the final diff to ensure unrelated provider and workspace changes remain untouched.

## Non-Goals

- Automatic verification orchestration or repair behavior.
- Automatic Human Play Review or Promote.
- C21 waiting-for-input, amendment, or drift work.
- New UI layout or styling.
