# C10/C12 Real Runtime — Implementation Plan

## Task 1 — TDD contracts

- [x] Add settings/provider-selection tests.
- [x] Add OpenGame path/configuration and hook-prompt tests.
- [x] Add CDP frame/evidence tests and a real Chrome smoke test guarded by
  explicit opt-in plus executable availability.
- [x] Confirm new tests fail before implementation.

## Task 2 — C10 runtime wiring

- [x] Add production settings and provider factory behavior.
- [x] Wire OpenGameAdapter into `create_app` without fake fallback.
- [x] Improve CLI resolution, configuration failure, hook prompt and checksum flow.

## Task 3 — C12 browser verifier

- [x] Extract shared evidence constants from Fake runner.
- [x] Implement Chrome CDP browser runner and artifact/workspace validation.
- [x] Wire it into the production app and remove API-level fake fallbacks.

## Task 4 — Verification

- [x] Run focused C10/C12 tests and real Chrome smoke; OpenGame credentialed
  smoke remains skipped when credentials are unavailable.
- [x] Run all backend tests and frontend typecheck/build.
- [x] Record skipped real-provider checks honestly and run `git diff --check`.
