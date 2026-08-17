# C14 Playable Version Promotion — Design Spec

Date: 2026-08-17
Status: Approved by user
Scope: FastAPI backend only

## Goal

After platform verification, require an explicit Human Play Review before a
`BuildCandidate` can become an immutable `PlayableVersion`. Support Restore as
a new candidate without rewriting version history or changing the current
playable until the normal verification and promotion gates pass again.

## Existing boundaries to preserve

- `BuildCandidate` is produced by C11 and verified by C12.
- `TestReport.platform_verdict` and `BuildCandidate.test_gate_status` are the
  platform-owned verification truth.
- `Project.current_playable_version_id` is the only current playable pointer.
- `PlayableVersion` and `Release` remain append-only records.
- Frontend, provider adapters, and GameSpec content do not own promotion state.

## Data model

### HumanPlayReview

One review record per candidate, keyed by a unique `candidate_id`:

- `decision`: `pending`, `accepted`, or `rejected`;
- `notes`: optional creator note;
- `amendment_status`: `not_required`, `confirmed`, or `unconfirmed`;
- `drift_status`: `clear` or `unresolved`;
- `reviewed_at`, `created_at`, `updated_at`.

The review is a workflow audit record, not part of `CreatorGameSpec`.

### BuildCandidate provenance

Add nullable `source_playable_version_id`. Restore candidates point to the
version they copied; normal build candidates leave it null. Existing artifact
path/checksum fields remain the candidate-owned provenance used by Promote.

## Service rules

`ProjectLifecycleService.promote_candidate` loads all gate records itself. It
rejects a candidate unless:

1. the build/candidate status is `succeeded`;
2. a persisted `TestReport` exists with `platform_verdict == PASSED`;
3. `test_gate_status == ready`;
4. Human Play Review is `accepted`;
5. amendment status is `confirmed` or `not_required`;
6. drift status is `clear`;
7. artifact path and checksum are present.

The service snapshots candidate provenance into a new `PlayableVersion`, sets
the parent to the current pointer, marks the candidate promoted, and updates
the project pointer in one transaction. A candidate's unique PlayableVersion
constraint makes repeated Promote return the original version.

## Restore

Restore loads a PlayableVersion belonging to the requested project, finds its
source candidate/build/spec revision, and creates:

- a new terminal `Build` with `operation = restore`;
- a new succeeded `BuildCandidate` with `test_gate_status = untested` and
  `source_playable_version_id` set;
- no TestReport, PlayableVersion, pointer, or Release mutation.

The new candidate must use the C12 test endpoint, then receive a new Human Play
Review, then be promoted. Restore is idempotent by `(project, source_version)`
while the generated candidate is still unpromoted.

## API

- `POST /api/v1/candidates/{candidate_id}/human-play-review`
- `GET /api/v1/candidates/{candidate_id}/human-play-review`
- `POST /api/v1/candidates/{candidate_id}/promote`
- `POST /api/v1/projects/{project_id}/playable-versions/{version_id}/restore`

All failures use the existing API error envelope and HTTP 409 for gate
violations.

## Non-goals

No Vue changes, automatic Promote, publish changes, generic workflow engine,
Amendment/Drift detection engine, or provider-specific logic.
