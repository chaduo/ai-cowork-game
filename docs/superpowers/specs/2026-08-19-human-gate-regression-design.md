# Silent Verification And Human Gate Repair Design

**Date:** 2026-08-19
**Scope:** Automatic platform verification and repair orchestration with explicit Human Gates

## Goal

Restore a buildable frontend and make platform Verification run silently after every successful Candidate build. A failed verification automatically creates a repair Build and verifies its replacement Candidate, for at most three repair rounds. A passing Candidate stops at Human Play Review; both Human Play Review and Promote remain explicit user actions.

## Existing Foundation

- `CandidateTestService` already persists platform-owned TestReports and evidence.
- Candidate repair ancestry and the three-round maximum already exist.
- `rebuildRemoteCandidate` already creates a replacement Build and records its repair link.
- Candidate preview, Human Play Review, and Promote APIs already exist.

This change connects those capabilities. It does not create a second verification or repair system.

## Changes

1. Restore the component-local `humanReviewNotes` ref in `K02ProjectWorkspace.vue`.
2. Remove the unused `autoDeliveryStatus` prop and any claim that Human Play Review or Promote completes automatically.
3. Replace the manual platform-verification button with automatic orchestration when a remote Candidate enters `untested`.
4. After a failed or invalid TestReport, build a replacement Candidate automatically, link it to its failed parent, then verify it automatically.
5. Include the failed report summary, diagnostics, and failed/missing evidence in the repair Build request so the Agent receives a scoped repair brief rather than the generic initial-build prompt.
6. Stop after three repair rounds. Preserve all Candidate and TestReport records, keep the current Playable unchanged, and show the terminal failure with an explicit user retry action.
7. Add an optional browser-test detail surface. It shows the Candidate iframe and honest verification state while testing, followed by the persisted evidence after completion. It does not claim to stream the backend Chrome process.

## State Flow

```text
Build succeeds
  -> Build Candidate
  -> automatic Platform Verification
  -> PASS -> explicit Human Play Review accept/reject
  -> explicit Promote after acceptance
  -> current Playable

Verification failure
  -> persist immutable failure evidence
  -> automatic repair Build with failure context
  -> replacement Candidate + repair ancestry
  -> automatic Platform Verification
  -> stop after at most three repair rounds
```

At no point may frontend presentation imply that the last two transitions are automatic.

## Orchestration Rules

- Only one verification/repair orchestration may own a Candidate in the current frontend session.
- Completed TestReports are reused through the existing idempotent API behavior.
- Every replacement Candidate must be linked before its verification begins.
- `ready` opens Human Play Review and ends automatic orchestration.
- `failed` or `invalid` triggers repair only while `repair_round < 3`.
- Automatic orchestration never calls Human Play Review or Promote APIs.

## Error Handling

- Review submission errors continue to render through the existing `reviewError` state.
- Promote errors continue to render through the existing `promoteError` state.
- Notes remain optional and local until the user submits an accept or reject decision.
- A verification transport/provider error stops the current automatic attempt and exposes a retry action; it is not counted as a verified repair failure without a persisted TestReport.
- A repair Build or repair-link error stops the loop and preserves the failed Candidate and its evidence.
- Hitting the three-round limit is an expected terminal state, not an infinite retry.

## Verification

- Use the current failing `npm run build` result as the `humanReviewNotes` regression reproduction.
- Add frontend contract tests for PASS stop, failure repair, replacement verification, transport-error stop, and the three-round terminal state.
- Add or extend backend/API tests proving idempotent TestReport reuse, immutable ancestry, failure-context propagation, and the hard repair limit.
- Run all frontend contract tests and the frontend production build.
- Run focused backend candidate/build tests, followed by the full non-browser backend suite.
- Inspect the final diff to ensure unrelated Game Design provider changes remain untouched.

## Non-Goals

- Automatic Human Play Review or Promote.
- C21 waiting-for-input, amendment, or drift work.
- Streaming screenshots or video from the backend Chrome process.
- A new background queue or distributed worker.
