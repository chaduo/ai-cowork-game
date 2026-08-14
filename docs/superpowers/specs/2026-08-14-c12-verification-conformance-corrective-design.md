# C12 Verification Conformance Corrective Design

## Goal

Make Candidate verification platform-owned and aligned with the frozen V1
contract without adding a browser driver or changing the Promote boundary.

## Contract decisions

- The authoritative platform verdict is one of `PASSED`, `PARTIAL_FAILURE`,
  `CRITICAL_FAILURE`, or `INVALID`.
- Runtime verdicts remain claims (`pass`, `fail`, `unknown`). A runtime claim
  cannot make a candidate ready.
- Evidence stores `source` (`platform` or `runtime`) and `severity`
  (`partial` or `critical`). A passing report requires platform-sourced
  evidence, one row for each required check, safe artifact references, and a
  validated `window.__GAME_TEST__` hook.
- Required checks cover a platform Build Check, Browser Smoke
  (`browser_started`, `console`), and Core Gameplay Acceptance
  (`core_input`, `gameplay`, `completion`, `phaser_hook`).
- Reports are immutable and idempotent per candidate. Failed or invalid
  candidates never change the Project playable pointer.
- Repair ancestry has an explicit `repair_round`; at most three repair rounds
  can be linked after the initial candidate. Each replacement remains a new
  candidate attempt.

## Boundaries

This corrective change only touches C12 persistence, contracts, service/API
responses, and tests. It does not add Playwright, OpenGame subprocesses,
Promote, Publish, or Workspace UI.

## Verification

The focused suite covers all four verdicts, platform-vs-runtime evidence,
artifact and Phaser hook validation, report idempotency, current playable
immutability, and the repair limit. The full backend suite and frontend build
remain regression gates.
