# C08/C09 Conformance Corrective Design

**Date:** 2026-08-14
**Status:** Approved direction, implementation pending
**Changes:** C08 `opengame-cli-spike`, C09 `opengame-process-executor`

## Goal

Close the evidence and executor gaps found in the C08/C09 review so C10 can integrate the pinned OpenGame CLI without relying on machine-specific paths, untrusted fixtures, truncated terminal events, or ambiguous process ownership.

## Constraints

- Keep OpenGame pinned as the `vendor/opengame` git submodule at commit `c54307efe1dab927e7fc52dbb92af6b3df1d1c66`.
- Do not modify OpenGame source.
- Do not add backend runtime dependencies.
- Keep Project, GameSpec, Candidate, Playable, Vue, and FastAPI repository types out of the executor.
- Preserve explicit argv execution through `asyncio.create_subprocess_exec`; never use `shell=True`.
- Support developer verification on macOS/Linux and Windows.
- Keep credentials in environment variables or ignored `.env.local` files and out of command strings, fixtures, logs, and Git.

## Considered Approaches

### A. Documentation-only correction

Update the C08 README, replace the invalid fixture, and leave C09 unchanged. This is the smallest change, but C10 would still receive output only after process completion, could lose the final `result` event after truncation, and would inherit cancellation races.

### B. Focused C08/C09 contract correction (selected)

Make the spike runner resolve the repository-pinned CLI, record portable sanitized fixtures, and extend the executor with line delivery while retaining bounded final diagnostics. Enforce one in-flight process per executor instance and make cancellation safe before, during, and after spawn. This keeps C09 provider-neutral while giving C10 the primitives it actually needs.

### C. Fold fixes into C10

Let OpenGameAdapter work around the executor and fixture problems. This would mix process lifecycle policy with provider parsing, duplicate buffering/cancellation logic, and leave C09's acceptance claims inaccurate.

Approach B is selected because it repairs each Change at its ownership boundary without broadening into C10 business mapping.

## C08 Evidence Design

### Pinned CLI resolution

All repeatable commands resolve OpenGame in this order:

1. `OPENGAME_CLI_JS`, when explicitly supplied for a developer override.
2. `<repository>/vendor/opengame/dist/cli.js`, the canonical pinned source.
3. A globally installed package only as a diagnostic fallback, never as conformance evidence.

The documented setup uses `git submodule update --init vendor/opengame`, verifies the gitlink commit, and invokes `node vendor/opengame/dist/cli.js`. It does not use `npm link`, a shallow clone of moving `main`, or a developer-specific absolute path.

### Portable fixture capture

Replace the machine-specific scripts with one Bash entry point that accepts a scenario and workspace root. Platform-specific tree termination remains C09's concern; C08 fixtures use the executor smoke where possible. The capture command writes to a temporary workspace, records exit status separately, and sanitizes absolute paths, session IDs, model endpoint details, and reasoning blocks before updating committed fixtures.

Committed fixtures remain valid NDJSON and contain only the minimum fields required by C10 parser tests. Raw provider output stays local and ignored.

### Capability matrix

The C08 report will contain an evidence-backed matrix for:

- `create`: supported through a fresh workspace and prompt.
- `modify`: supported only when a confirmed baseline is copied into a fresh run workspace and the request describes a bounded change; evidence must show the baseline and changed artifact.
- `resume`/`continue`: recorded as provider session capabilities, not used as the platform's durable recovery mechanism unless separately proven.
- `cancel`: executor-owned process termination; OpenGame emits no reliable terminal event.
- `timeout`: executor-owned deadline termination; partial artifacts are rejected.
- unsupported operations: every requested operation without real CLI evidence is explicitly listed as unsupported rather than mapped to success.

The invalid-output fixture must match its documented prompt, workspace, and output tree. Fixture metadata records scenario, CLI commit, command shape, exit code, and artifact check.

## C09 Executor Design

### Single-run ownership

An `AsyncSubprocessExecutor` instance owns at most one in-flight process. A second concurrent `run()` call fails immediately with a typed executor-busy error. C10 must allocate one executor per Build run or use an explicit factory. This prevents one Project's run or cancellation from overwriting another Project's process handle.

### Spawn-safe cancellation

Cancellation is represented by an `asyncio.Event` that exists before spawning begins. `run()` checks it before spawn and immediately after the process handle is installed. `cancel()` sets the event first and kills the current process tree when present. A request racing with process creation therefore cannot be lost.

Natural completion wins only if the process exited before cancellation was requested. Cancellation after a completed result does not rewrite a successful result as cancelled.

### Incremental output and bounded diagnostics

The executor accepts optional async line callbacks for stdout and stderr. Drain tasks decode complete lines incrementally and invoke the callbacks while the process runs. This is the provider-neutral primitive C10 will use to parse OpenGame NDJSON and persist C07 RunEvents in real time.

`ProcessResult.stdout` and `stderr` remain bounded diagnostic previews. Truncation affects only these previews, not callback delivery. The implementation preserves a tail window so the final diagnostic still contains terminal context, while C10 receives every complete stdout line through the callback.

Callback failures terminate the process tree and propagate as execution errors; they are never converted into a successful process result.

### Process termination

- POSIX: start a new session and terminate the process group, escalating to kill after a bounded grace period.
- Windows: call `taskkill /T /F`, verify its return code, then fall back to killing the direct process if the tree command fails.
- In all cases, failure to reap the process is surfaced; the executor must not report `timed_out` or `cancelled` while knowingly leaving the direct child running.

Launch failures such as a missing command remain explicit exceptions for C10 to map to the provider-neutral `unsupported` or `failed` result. They are not fabricated as exit code zero.

## Interfaces

The existing `ProcessResult` fields remain compatible:

```python
stdout: str
stderr: str
exit_code: int | None
process_status: Literal["completed", "timed_out", "cancelled"]
duration_seconds: float
output_truncated: bool
```

`ProcessExecutor.run()` adds optional callbacks:

```python
async def run(
    *,
    command: str,
    arguments: list[str],
    cwd: str,
    approved_env: dict[str, str],
    timeout: float | None,
    on_stdout_line: AsyncLineCallback | None = None,
    on_stderr_line: AsyncLineCallback | None = None,
) -> ProcessResult: ...
```

Where:

```python
AsyncLineCallback = Callable[[str], Awaitable[None]]
```

The fake executor records the same inputs and emits its canned lines through the callbacks so C10 can share one contract suite.

## Error Handling

- Invalid `cwd`, missing executable, and permission failures raise their original OS error with no success result.
- A timeout returns `process_status="timed_out"` only after termination and reap complete.
- Explicit cancellation returns `process_status="cancelled"` only after termination and reap complete.
- A callback/parser failure kills the process and re-raises the callback error.
- A second concurrent run raises `ExecutorBusyError` without touching the active process.
- Truncated diagnostic previews set `output_truncated=True`; line callbacks remain complete.

## Testing

### Automated executor tests

- Existing stdout, stderr, exit code, cwd, env allowlist, and no-shell tests remain.
- A cancellation requested while spawn is delayed prevents the child from continuing.
- Cancellation racing after natural completion does not rewrite the result.
- Concurrent `run()` calls reject the second call and do not cross-cancel.
- Stdout callback receives the final NDJSON `result` line even when diagnostic preview truncates.
- Callback failure terminates the process.
- Timeout and cancellation prove the process tree is gone.
- Fake and real executors satisfy the callback-compatible contract.

### C08 evidence tests

- CLI resolver selects `vendor/opengame/dist/cli.js` from a clean checkout.
- Every committed NDJSON fixture parses line by line.
- Sanitized fixtures contain no absolute developer paths, credentials, session UUIDs, or reasoning blocks.
- Scenario metadata and fixture contents agree for success, failure, cancel, timeout, invalid output, and modify.
- Clean environments skip only credentialed full generation; the pinned `--help` smoke runs whenever the submodule is initialized.

### Verification commands

```bash
git submodule update --init vendor/opengame
backend/.venv/bin/pytest backend/tests/test_c09_executor.py -q
backend/.venv/bin/pytest backend/tests/test_c09_executor_smoke.py -q -rs
backend/.venv/bin/pytest backend/tests -q
npm --prefix frontend run build
```

The credentialed create/modify smoke remains opt-in, but its absence is reported as an explicit verification gap rather than silently treated as C08 acceptance.

## Completion Gate

C08 is conformant only when the create and modify evidence, unsupported matrix, portable setup, and sanitized fixtures agree with one another. C09 is conformant only when its full deterministic suite passes and the pinned no-credential OpenGame smoke runs from `vendor/opengame`. C10 must not begin implementation against this branch until both gates pass or the remaining credentialed evidence gap is explicitly accepted by the human reviewer.
