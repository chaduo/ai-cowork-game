# Run Event Observability Design

## Goal

Persist normalized run state and ordered events so status queries, page refreshes, and SSE reconnects all read
the same run without starting another build.

## Data model

Add `runs` and `run_events` tables. A Run stores the stable `run_id`, `build_id` reference, status,
`last_sequence`, cancellation timestamp, terminal error, and lifecycle timestamps. A RunEvent stores the
normalized C06 event fields plus serialized structured error. `(run_id, sequence)` is unique and indexed.
Run status is one of `running`, `cancelling`, `succeeded`, `failed`, `cancelled`, `timed_out`,
`invalid_output`, `unsupported`, or `orphaned`; only the last six plus `orphaned` are terminal.

## Repository rules

`RunRepository.create_run` is idempotent by `run_id`. `append_event` requires the next exact sequence, rejects
events after terminal state, sanitizes messages/error details before storage, and never changes terminal status
from event text. `finish_run` changes state only when the caller supplies a terminal event and a standard
terminal status; success requires a `completed` event with an artifact reference. `request_cancel` moves a
running run to `cancelling` and emits a platform cancellation-request event; only provider confirmation can
make it `cancelled`. `recover_orphaned_runs` marks non-terminal runs orphaned after a process restart and never
marks them succeeded.

## HTTP and SSE

- `POST /api/v1/runs` creates or returns a run by stable `run_id`.
- `GET /api/v1/runs/{run_id}` returns persisted status and `last_sequence`.
- `GET /api/v1/runs/{run_id}/events?after_sequence=N` returns ordered replay JSON.
- `GET /api/v1/runs/{run_id}/events/stream` emits SSE `id`, `event: run_event`, and JSON data. It honors
  `after_sequence` or `Last-Event-ID`, polls persisted state for a bounded window, and closes after terminal
  state or idle timeout. Reconnect therefore asks for the next sequence instead of creating a run.
- `POST /api/v1/runs/{run_id}/cancel` requests cancellation and does not claim terminal success.

The event ingestion and terminal transition methods are repository-owned; no provider logs or raw diagnostics
are exposed by this change. Workspace UI, OpenGame parsing, BuildCandidate promotion, and SSE frontend wiring
remain out of scope.

## Testing

Repository tests cover idempotent run creation, exact sequence ordering, replay, sanitization, terminal guards,
cancel/orphan recovery, and no-fake-success behavior. API tests cover status, JSON replay, SSE reconnect, and
cancel. Existing C01-C06 tests and frontend build remain required regression checks.
