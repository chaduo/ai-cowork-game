# C16 — Release Publishing Verification

**Date:** 2026-08-18
**Branch:** `codex/c16-release-publishing`
**Base:** `origin/main` at `4855c70` (C15 merged)

## Delivered

C16 now provides a persisted vertical slice:

```text
current Playable
  -> Publish Review (read-only eligibility and provenance)
  -> explicit Human Publish
  -> immutable Release snapshot
  -> honest empty ResourceExtractionBatch boundary
  -> Release detail and refresh recovery
```

The existing Workspace modal and drawer remain the visual surface. Remote projects use the API-backed state; deterministic demo screens retain their existing local fixtures.

## Backend Contract

Migration `0015_c16_release_publishing` adds immutable Release snapshot fields:

- `name`, `description`
- `game_design_revision_id`, `gamespec_revision_id`
- `artifact_path`, `artifact_checksum`
- existing `git_commit` provenance

It also adds one `ResourceExtractionBatch` per Release. C16 intentionally creates an `empty` batch with `candidate_count=0`; ResourceCandidate rows belong to C17 and are never invented by the publish action.

Routes:

- `GET /api/v1/projects/{project_id}/publish-review`
- `GET /api/v1/projects/{project_id}/releases`
- `GET /api/v1/projects/{project_id}/releases/{release_id}`
- `POST /api/v1/projects/{project_id}/releases`

The POST transition is explicit and idempotent by `(project_id, playable_version_id)`. Repeating it returns the existing Release and does not overwrite its snapshot. A non-current Playable, a missing Playable, or a missing provenance guard is rejected without changing the current Playable.

## Verification Evidence

Focused backend coverage:

```text
backend/.venv/bin/pytest backend/tests/test_c16_release_api.py \
  backend/tests/test_c16_release_schema.py \
  backend/tests/test_c14_api.py \
  backend/tests/test_c20_checkpoint.py -q
30 passed
```

Full backend suite excluding the known local browser-launch permission file:

```text
backend/.venv/bin/pytest backend/tests -q \
  --ignore=backend/tests/test_browser_runner_real_candidate.py
346 passed, 8 skipped, 1 warning
```

The ignored file contains two real Playwright tests that fail on this macOS environment before a page is created. Chromium exits with:

```text
FATAL:base/apple/mach_port_rendezvous_mac.cc:159
Check failed: kr == KERN_SUCCESS. bootstrap_check_in ... Permission denied (1100)
```

This is an OS/browser sandbox limitation, not a C16 assertion or API failure. The tests must still be run on a machine where Playwright Chromium can launch before calling browser acceptance complete.

Frontend verification:

```text
for f in frontend/tests/*.test.mjs; do node "$f"; done
# all 15 subtests pass

npm --prefix frontend run build
# vue-tsc -b and Vite build pass
```

The release mapping tests cover API snake_case mapping, empty-batch count, and Publish Review draft hydration. Existing routing tests cover preservation of the promoted playable while a later build fails.

## Manual Acceptance Checklist

Run against a clean database with the backend and frontend dev servers started:

1. Open a project with a current promoted Playable.
2. Open Publish Review and confirm the source Playable, Game Design revision, GameSpec revision, artifact path/checksum and next release number are visible.
3. Close the review without publishing; verify no Release is created.
4. Publish once; verify the Release detail opens and shows immutable provenance.
5. Refresh the page and reopen the project; verify the same Release is restored.
6. Publish the same Playable again; verify the same Release id is returned.
7. Confirm the resource section says there are no new resources to review, rather than showing a fabricated pending count.
8. Create a later failed/cancelled build; verify the existing Release and current Playable remain unchanged.

Manual browser completion is still environment-dependent until the Playwright launch permission issue above is cleared.

## C17 Boundary

C16 persists the Release-to-resource-extraction boundary only. It does not create ResourceCandidate records, matching decisions, or a Resource Review workflow. Those belong to C17 and must consume the immutable Release and its extraction batch rather than re-running publish.
