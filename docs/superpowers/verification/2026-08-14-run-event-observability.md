# C07 Run Event Observability Verification

## Automated

```bash
VENV=/Users/zhaozhuo/workspace/explore/ai-cowork-game/.worktrees/platform-backend-foundation/backend/.venv/bin
"$VENV/pytest" backend/tests -q
npm --prefix frontend run build
git diff --check
```

The C07 repository/API tests cover idempotent `run_id`, strict sequence and replay, diagnostic redaction,
terminal guards, cancellation, orphan recovery, JSON status, SSE `Last-Event-ID`, and error envelopes.

## Manual API smoke

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/runs \
  -H 'Content-Type: application/json' \
  -d '{"run_id":"manual-run-1","build_id":"manual-build-1"}'

curl -s http://127.0.0.1:8000/api/v1/runs/manual-run-1
curl -s 'http://127.0.0.1:8000/api/v1/runs/manual-run-1/events?after_sequence=0'
curl -i -N 'http://127.0.0.1:8000/api/v1/runs/manual-run-1/events/stream'
curl -s -X POST http://127.0.0.1:8000/api/v1/runs/manual-run-1/cancel
```

The second create call with the same `run_id` returns the same row. Status becomes `cancelling` after cancel;
it never becomes `succeeded` without an explicit terminal provider result. Event ingestion is repository-owned
until C11 connects the BuildService, so a fresh manual run has no events until a contract consumer appends them.
