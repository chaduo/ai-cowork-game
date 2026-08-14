# C08/C09 Conformance Corrective Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make C08 evidence portable and truthful, and make C09 safe for C10's real-time OpenGame integration.

**Architecture:** Keep `AsyncSubprocessExecutor` provider-neutral and single-run. Add asynchronous line callbacks so C10 can consume complete NDJSON while bounded stdout/stderr remain diagnostics only. Resolve C08 smoke commands from the pinned `vendor/opengame` gitlink and validate committed fixtures through deterministic hygiene tests.

**Tech Stack:** Python 3.11, asyncio subprocesses, pytest, Bash, Git submodules, OpenGame 0.6.0 NDJSON.

## Global Constraints

- OpenGame stays pinned at `vendor/opengame` commit `c54307efe1dab927e7fc52dbb92af6b3df1d1c66`.
- Do not modify OpenGame source or add runtime dependencies.
- Never execute provider commands through a shell.
- Keep credentials out of argv, committed fixtures, logs, and Git.
- Support macOS/Linux and Windows process execution.
- Keep C10 provider parsing and business mapping out of C09.

---

### Task 1: Executor streaming and bounded diagnostics

**Files:**
- Modify: `backend/app/agents/executor.py`
- Modify: `backend/app/agents/subprocess_executor.py`
- Modify: `backend/app/agents/fake_executor.py`
- Test: `backend/tests/test_c09_executor.py`

**Interfaces:**
- Produces: `AsyncLineCallback = Callable[[str], Awaitable[None]]`
- Produces: optional `on_stdout_line` and `on_stderr_line` arguments on `ProcessExecutor.run()`
- Preserves: existing `ProcessResult` fields and existing callers

- [ ] **Step 1: Add failing tests for incremental stdout/stderr callbacks**

Add tests that start a real Node process, emit two newline-delimited messages, and assert callback order. Add a large-output test whose diagnostic preview truncates while its callback still receives a final `{"type":"result"}` line.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
backend/.venv/bin/pytest backend/tests/test_c09_executor.py -q
```

Expected: callback arguments are rejected by the current `run()` signature.

- [ ] **Step 3: Implement callback-compatible draining**

Add the callback type to `executor.py`. Decode stdout/stderr incrementally by complete lines, await callbacks in stream order, retain bounded diagnostic previews, and preserve a small tail when truncated. Callback exceptions must kill the process and propagate.

- [ ] **Step 4: Update `FakeProcessExecutor`**

Accept the same callback arguments and deliver canned stdout/stderr lines through them. Continue recording the inputs used by contract tests.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run the Task 1 test file and confirm all existing and new cases pass.

- [ ] **Step 6: Commit Task 1**

```bash
git add backend/app/agents backend/tests/test_c09_executor.py
git commit -m "fix: stream executor output safely"
```

### Task 2: Spawn-safe cancellation and single-run ownership

**Files:**
- Modify: `backend/app/agents/executor.py`
- Modify: `backend/app/agents/subprocess_executor.py`
- Test: `backend/tests/test_c09_executor.py`

**Interfaces:**
- Produces: `ExecutorBusyError`
- Guarantees: one in-flight process per executor instance
- Guarantees: cancellation cannot be lost during spawn

- [ ] **Step 1: Add failing lifecycle tests**

Add tests for:

```text
cancel requested while subprocess creation is delayed
second run rejected while first run remains active
cancel after natural completion does not rewrite completed to cancelled
```

Use real Node processes for ownership behavior and a narrowly patched subprocess creation coroutine only for the pre-spawn race.

- [ ] **Step 2: Run focused tests and verify RED**

Expected: the second run overwrites `_proc`, or the pre-spawn cancellation does not finish.

- [ ] **Step 3: Implement lifecycle state**

Use an `asyncio.Lock` for state transitions and an `asyncio.Event` for cancellation. Reject a second active run with `ExecutorBusyError`. Check cancellation before spawn and immediately after installing the process handle. Clear the active handle only when the owning run finishes.

- [ ] **Step 4: Harden process-tree termination**

Check Windows `taskkill` status, fall back to direct `proc.kill()` when necessary, and raise if the direct child cannot be reaped. On POSIX, handle a vanished process group without changing a natural completion into cancellation.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run `backend/tests/test_c09_executor.py -q` and confirm no orphan process remains.

- [ ] **Step 6: Commit Task 2**

```bash
git add backend/app/agents backend/tests/test_c09_executor.py
git commit -m "fix: make executor cancellation race safe"
```

### Task 3: Pinned OpenGame smoke and C08 evidence conformance

**Files:**
- Modify: `backend/tests/test_c09_executor_smoke.py`
- Create: `backend/tests/test_c08_evidence.py`
- Create: `docs/development/c08-opengame-spike/capture-fixture.sh`
- Modify: `docs/development/c08-opengame-spike/README.md`
- Modify: `docs/development/c08-opengame-spike/success-fixture-README.md`
- Modify: `docs/development/c08-opengame-spike/*-run.stream.json`
- Remove: redundant machine-specific capture scripts after their behavior is represented by `capture-fixture.sh`

**Interfaces:**
- Smoke resolver uses `<repo>/vendor/opengame/dist/cli.js` first
- `OPENGAME_CLI_JS` remains an explicit developer override
- Evidence tests define accepted fixture hygiene and capability-matrix truthfulness

- [ ] **Step 1: Add failing smoke resolver tests**

Test that a temporary repository-shaped directory containing `vendor/opengame/dist/cli.js` is selected without a global npm link, and that an explicit override wins.

- [ ] **Step 2: Add failing evidence hygiene tests**

For every committed NDJSON fixture, assert line-by-line JSON validity and absence of developer absolute paths, API keys, raw session UUID values, and `thinking` content blocks. Assert the README contains explicit create/modify/cancel/timeout/invalid-output/unsupported conclusions.

- [ ] **Step 3: Verify RED**

Run:

```bash
backend/.venv/bin/pytest backend/tests/test_c09_executor_smoke.py backend/tests/test_c08_evidence.py -q -rs
```

Expected: pinned resolver and evidence hygiene assertions fail.

- [ ] **Step 4: Implement repository-pinned CLI resolution**

Refactor the smoke helper to accept a repository root, prefer `OPENGAME_CLI_JS`, then use `vendor/opengame/dist/cli.js`. Keep global lookup only as an explicitly non-conformant fallback.

- [ ] **Step 5: Replace capture scripts and sanitize fixtures**

Create one path-independent script that takes `success`, `failure`, `invalid-output`, `timeout`, or `cancel`; uses a temporary workspace; invokes `node "$CLI"` with credentials inherited through the environment; records exit status; and never interpolates secrets into a PowerShell command. Convert committed fixtures to minimal sanitized NDJSON while preserving parser-relevant fields and terminal/non-terminal shapes.

- [ ] **Step 6: Correct the capability matrix and provenance**

Document create as proven. Document modify as unsupported pending real evidence unless a credentialed run is performed during this task. Describe the actual invalid-output scenario represented by its fixture. Remove contradictory claims that `is_error=false` alone proves success.

- [ ] **Step 7: Run evidence and smoke tests GREEN**

The pinned `--help` test passes when the submodule is initialized. Credentialed generation may skip only with an explicit reason shown by `-rs`.

- [ ] **Step 8: Commit Task 3**

```bash
git add backend/tests docs/development/c08-opengame-spike
git commit -m "fix: make opengame evidence reproducible"
```

### Task 4: Full verification and closeout

**Files:**
- Modify: `docs/development/c08-opengame-spike/README.md` only if verification exposes a remaining evidence gap

- [ ] **Step 1: Initialize the pinned submodule when network access is available**

Run:

```bash
git submodule update --init vendor/opengame
```

Verify the checked-out commit is exactly `c54307e`.

- [ ] **Step 2: Run backend verification**

```bash
backend/.venv/bin/pytest backend/tests/test_c09_executor.py backend/tests/test_c09_executor_smoke.py backend/tests/test_c08_evidence.py -q -rs
backend/.venv/bin/pytest backend/tests -q
```

- [ ] **Step 3: Run frontend verification**

```bash
npm --prefix frontend ci
npm --prefix frontend run build
```

- [ ] **Step 4: Run static checks**

```bash
bash -n docs/development/c08-opengame-spike/capture-fixture.sh
git diff --check origin/main...HEAD
git status --short
```

- [ ] **Step 5: Record honest residual evidence**

If credentials are unavailable, keep modify marked unsupported/pending evidence and report the credentialed smoke skip. Do not call C08 fully accepted until human review accepts that limitation.

- [ ] **Step 6: Commit closeout documentation if changed**

```bash
git add docs/development/c08-opengame-spike/README.md
git commit -m "docs: record c08 c09 verification"
```

## Self-Review

- Every production behavior change starts with a focused failing test.
- C08 documentation changes are backed by evidence-hygiene tests.
- C09 stays provider-neutral; OpenGame parsing remains C10 work.
- Existing `ProcessResult` consumers remain source-compatible through optional callbacks.
- Missing credentials produce a visible skip and an unsupported/pending conclusion, never a fabricated pass.
