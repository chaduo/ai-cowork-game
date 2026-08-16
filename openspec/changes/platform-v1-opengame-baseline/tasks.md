## 1. Shared Contracts and Spikes

- [ ] 1.1 Scaffold Vue, FastAPI, Phaser template, deployment, and test directories with pinned toolchain versions.
- [ ] 1.2 Define runtime command/result, RunEvent, Candidate, TestReport, and Version schemas with serialization tests.
- [ ] 1.3 Implement a Fake Runtime and a provider-neutral contract test suite for create, modify, cancel, events, artifacts, and failures.
- [x] 1.4 Spike the real OpenGame CLI to fix its version, non-interactive invocation, output mapping, workspace behavior, timeout, and cancellation contract. — Done 2026-08-14: pinned `CodingZY/OpenGame`@`c54307e` (`opengame` v0.6.0), real game generated, success fixture `docs/development/c08-opengame-spike/success-run.stream.json`. Non-interactive args: `opengame -p "<prompt>" --yolo --auth-type openai -m <model> -o stream-json`, cwd = run workspace. stream-json = NDJSON `system`/`assistant`/`result` → RunEvent. Remaining: failure/cancel/invalid-output/timeout fixtures.
- [ ] 1.5 Pin OpenGame as `vendor/opengame` submodule at commit `c54307e`; remove the mislabeled `test/agent-game-forge` submodule; update README/CONTRIBUTING to point at `vendor/opengame`. (Contract/docs change; OpenGame source stays in the submodule, never copied into the main repo.)

## 2. Persistent Platform Workflow

- [ ] 2.1 Add SQLite migrations and repositories for projects, runs, events, Candidates, TestReports, Versions, and the single-active-run guard.
- [ ] 2.2 Implement the deterministic GDD confirmation, GameSpec confirmation, asset acceptance, coding, build, test, and publication state transitions.
- [ ] 2.3 Add startup recovery that fails orphaned runs and enables clean retry from the playable Version.
- [ ] 2.4 Implement REST and SSE endpoints for project gates, runs, cancellation/retry, Candidates, TestReports, Versions, and preview metadata.

## 3. Candidate-to-Version Vertical Slice

- [ ] 3.1 Implement trusted project Git repositories plus workspace export without trusted `.git` or platform source.
- [ ] 3.2 Implement Candidate snapshots, ancestry, status changes, diagnostics, and allowlisted import validation.
- [ ] 3.3 Build the fixed Phaser survival template and validated GameSpec loader with deterministic NPC behavior.
- [ ] 3.4 Add the read-only test bridge and Chromium checks for build, page load, console errors, movement, enemy loop, items, NPC interaction, and game outcome.
- [ ] 3.5 Implement TestReport validation that rejects missing or contradictory PASS evidence.
- [ ] 3.6 Implement atomic PASS-only Git Version publication, artifact storage, and playable pointer update.
- [ ] 3.7 Add failure/cancellation integration tests proving the prior playable artifact never changes.

## 4. Isolation and OpenGame Baseline

- [x] 4.1 Implement the restricted runner with workspace-only mounts, non-root execution, resource/time/output limits, and approved network/environment policy. — Done 2026-08-15 (path/workspace/cancel-cleanup portion): real per-run workspace `data/workspaces/{run_id}/{session_id}` created + persisted (`Run.workspace_path`/`workspace_status`, migration `0011_c13_workspace`); `WorkspaceManager` prepares/discards; BuildService prepares before agent.start, discards on cancel/failure/timeout/invalid_output/orphan, and retry gets a fresh run_id → fresh workspace (never reuses a partial). Output is capped by the C09 executor (`DEFAULT_OUTPUT_LIMIT_BYTES`) and env is the C09 allowlist. **Deferred to a later slice per `design.md:97`**: container/docker sandbox, network egress, CPU/mem/FD limits, non-root execution — V1-local is exported-workspace + path-guard with `GEMINI_SANDBOX=false`; container is an optional deploy-time flag (`-s`/`--sandbox-image`), out of C13's V1-local scope.
- [x] 4.2 Add path canonicalization, symlink/protected-path rejection, secret redaction, and audit tests. — Done 2026-08-15: `backend/app/agents/workspace.py` `validate_member` canonicalizes (realpath) and rejects absolute/`..`/symlink-escape/protected (`.git`/`.env`/`.env.local`) paths with a sanitized `WorkspaceEscapeError` (code preserved); `scan_preview` replaces the adapter's `_scan_artifacts` and maps an escape to `invalid_output` (no import). `backend/app/redaction.py` is the single redaction truth source (`runs.py.sanitize_text` delegates); raw `ProcessResult` buffers are redacted before diagnostics/events/artifact scan. Audit tests: `test_c13_workspace.py` (escape denial per vector, canonicalization, redaction, lifecycle) + `test_c13_build_workspace_lifecycle.py` (cancel/retry-no-partial/orphan discard). Two symlink-creation tests skip on a locked-down Windows box (WinError 1314) with a stated reason; the rejection logic runs on POSIX CI.
- [x] 4.3 Implement OpenGameAdapter using the pinned spike contract and normalized RunEvents. — Done 2026-08-15: `backend/app/agents/opengame_adapter.py` maps `GameBuildRequest`→`opengame` CLI (via C09 `ProcessExecutor`) and stream-json+`ProcessResult`→`RunEvent`/`GameBuildResult`. `SUPPORTED_OPERATIONS = {"create"}` (per C08 capability matrix: modify/repair/test return `unsupported` until new real evidence). Success is never inferred from `is_error` alone — decision combines `process_status`+`exit_code`, the parsed top-level `result` event (`[API Error:]`/zero-token check), and an independent `index.html` artifact existence check. Split into `opengame_stream_parser.py` (NDJSON→provider events) + `opengame_event_mapper.py` (→provider-neutral `RunEvent`, monotonic sequence, UTC timestamps, no Human-Gate kinds).
- [x] 4.4 Pass the shared runtime contract suite with OpenGame for create, incremental modify, cancellation, invalid output, and provider failure. — Done 2026-08-15: `OpenGameAdapter` passes the shared suite `assert_game_agent_contract` (create/unsupported/cancel) with `FakeProcessExecutor` (`test_c10_game_agent_contract.py`). The five C08 fixtures are replayed through `_build_result` to lock the load-bearing mapping rules — success→`succeeded`, failure (`[API Error:]`, usage 0)→`failed`, invalid-output (success, no `index.html`)→`invalid_output`, timeout→`timed_out`, cancel→`cancelled` (`test_c10_build_result_from_fixtures.py`). A real create run passed the smoke gate end-to-end via the real `opengame` CLI (`test_c10_opengame_adapter_smoke.py`, kimi-k3, 81.5s, exit 0). "incremental modify" is intentionally NOT exercised as `succeeded` — it returns `unsupported` until a real modify run is captured (C08 matrix); modify/repair/test each assert `unsupported`+`error.code=="unsupported_operation"` and the executor is never launched.
- [ ] 4.5 Capture repeatable OpenGame benchmark fixtures and measurements for three baseline runs.

## 5. User Workflow

- [ ] 5.1 Implement access-code session protection and public-preview separation.
- [ ] 5.2 Implement Vue views for idea input, GDD confirmation, GameSpec confirmation, asset review, run events, and cancellation.
- [ ] 5.3 Implement Candidate/TestReport/Version history and keep iframe preview pinned to the playable Version during failures.
- [ ] 5.4 Implement supported AI incremental modification and Monaco allowlisted edits as new Candidates.
- [ ] 5.5 Add browser acceptance coverage for initial creation, modification, direct edit, failure protection, retry, and restore.

## 6. Deployment and V1 Acceptance

- [ ] 6.1 Add Compose packaging, persistent volumes, health checks, proxy routing, public artifact hosting, and runner configuration.
- [ ] 6.2 Run the full automated suite from a clean environment and document exact setup and recovery commands.
- [ ] 6.3 Complete three OpenGame vertical-slice rehearsals and record success rate, timing, failure stages, usage, and TestReport outcomes.
- [ ] 6.4 Review and freeze the V1 runtime, Candidate/TestReport/Version, isolation, and RunEvent contracts required by V2.
