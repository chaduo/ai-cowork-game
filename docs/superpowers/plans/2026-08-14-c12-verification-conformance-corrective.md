# C12 Verification Conformance Corrective Plan

## Task 1: Extend persisted verification schema

- Add `source` and `severity` to TestEvidence, report `severity`, and
  `repair_round` to BuildCandidate.
- Add repeatable migration `0010_c12_verification_conformance` with legacy
  verdict normalization.
- Update schema tests for the new canonical values.

## Task 2: Enforce platform evidence and verdicts

- Extend the provider-neutral evidence contract and deterministic fixtures.
- Have the service add a platform-owned Build Check, validate safe artifact
  references and the Phaser `window.__GAME_TEST__` hook, and derive the four
  canonical verdicts.
- Keep report creation idempotent and never touch current playable state.

## Task 3: Bound repair ancestry and API shape

- Track repair rounds separately from the candidate attempt number.
- Reject links after three repair rounds while preserving all prior records.
- Expose source, severity, verdict and repair round in the candidates API.

## Task 4: Verify and document

- Add focused tests for all verdict paths, invalid artifacts, hook validation,
  runtime-only PASS and the repair limit.
- Run the full backend suite, frontend build, migration repeatability and
  `git diff --check`.
