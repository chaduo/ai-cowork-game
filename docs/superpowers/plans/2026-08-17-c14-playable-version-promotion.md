# C14 Playable Version Promotion — Implementation Plan

## Task 1 — TDD contract tests

- [x] Add service tests for every Promote blocker, idempotency, atomic pointer
  update, and Restore provenance/history.
- [x] Add API tests for review, promote, restore, error envelopes, and ownership.
- [x] Run the focused tests and confirm failures before implementation.

## Task 2 — Persistence

- [x] Add `HumanPlayReview` model and `BuildCandidate.source_playable_version_id`.
- [x] Add Alembic migration `0012_c14_playable_promotion`.
- [x] Add migration/schema assertions.

## Task 3 — Lifecycle service

- [x] Implement review upsert/read helpers.
- [x] Tighten Promote to load and validate persisted gates and snapshot Candidate
  provenance.
- [x] Implement Restore-as-new-Candidate without touching current Playable/Release.

## Task 4 — API surface

- [x] Add review, promote, and restore routes using the existing error envelope.
- [x] Return stable candidate/version summaries and preserve idempotent responses.
- [x] Add read-only Playable version history endpoint.

## Task 5 — Verification

- [x] Run C14 focused tests, then all backend tests.
- [x] Run `cd frontend && npx vue-tsc -b && npx vite build`.
- [x] Run `git diff --check` and review the final diff.
