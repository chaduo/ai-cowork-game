# C11 Build Context Corrective Verification

**Branch:** `codex/c11-build-job-orchestration`
**Base:** `origin/main` at `beb8985`
**Commit:** `7a5392a feat: persist immutable c11 build context`

## Verified behavior

- A Build creates one immutable Build Context before provider invocation.
- CreatorGameSpec and RuntimeBuildSpec are stored as canonical JSON with SHA-256 hashes.
- Affected scope, resource references, implementation dependencies and relevant overrides are persisted and passed through the C06 GameBuildRequest contract.
- Changing current playable, creating a later GameSpec revision or changing current Game Design status does not alter the stored request.
- Duplicate Build requests return the original context and do not replace task-scoped inputs.
- Retry creates a new Build Context with copied input snapshots and preserves the parent context.
- A successful Candidate links to exactly one Build Context; current Playable remains unchanged.
- Existing direct lifecycle/C12 Candidate fixtures remain compatible because the new provenance pointer is nullable for legacy rows.

## Verification commands

```text
VENV=/Users/zhaozhuo/workspace/explore/ai-cowork-game/.worktrees/platform-backend-foundation/backend/.venv/bin
$VENV/pytest backend/tests/test_c11_build_orchestration.py backend/tests/test_c11_build_api.py -q
# 17 passed, 1 warning

$VENV/pytest backend/tests -q
# 118 passed, 1 warning

DATABASE_URL="sqlite:////private/tmp/c11-context-repeatability.sqlite" \
  $VENV/alembic upgrade head
# executed twice against the same SQLite database without error

cd frontend && npm run build
# vue-tsc -b and Vite build passed

git diff --check
# no whitespace errors
```

## Scope guard

This Change only extends C11 persistence and provider request construction. It does not add OpenGame subprocesses, TestReport verdicts, Promote, Publish, Resource Review or Workspace UI behavior.
