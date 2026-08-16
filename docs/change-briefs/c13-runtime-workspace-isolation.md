# Change: c13-runtime-workspace-isolation

## 1. Metadata

**Change ID:** C13
**Owner:** zhang
**Reviewer:** zhao（Required Review）
**Priority:** P0
**Depends On:** C08 spike; C09 executor; C10 OpenGameAdapter (C13 wires into the adapter and BuildService on top of C10)
**Status:** Implemented on `feature/c13-runtime-workspace-isolation`

## 2. Goal

隔离 OpenGame 运行与生成代码，使其只能访问该 run 的 workspace 与批准环境；cancel/failure/orphan 后的 partial workspace 不被下一次 retry 信任或复用。满足 `platform-v1-opengame-baseline` tasks 4.1（restricted runner 的 workspace/cancel-cleanup 部分）与 4.2（path canonicalization、symlink/protected-path rejection、secret redaction、audit tests），并支撑 rebaseline 每日门禁「Confirmed GameSpec starts one real Build and creates one isolated Candidate」。

## 3. In Scope

- 真实 per-run workspace `data/workspaces/{run_id}/{session_id}` 的创建、持久化（`Run.workspace_path` + `Run.workspace_status`）与丢弃。
- 路径 canonicalization + 拒绝绝对/`..`/symlink-escape/受保护路径（`.git`、`.env`、`.env.local`），产生 sanitized `WorkspaceEscapeError` 审计证据。
- artifact 扫描改为 escape-safe（`WorkspaceManager.scan_preview` 替代 adapter 旧的 `_scan_artifacts`）；escape → `invalid_output` + 具体原因 code，不 import。
- 原始 `ProcessResult.stdout/stderr` 在进入 diagnostics / event / artifact 扫描前脱敏（复用 `app.redaction`，单一真相源，不截断）。
- cancel/failure/timeout/invalid_output/orphan 后丢弃 partial workspace；retry 用新 run_id → 新 workspace，不复用旧 partial。
- 审计测试（escape 拒绝、canonicalize、脱敏、生命周期、cancel/retry-no-partial、orphan 丢弃）。

## 4. Out of Scope

- 容器/docker 沙箱、网络出口策略、CPU/内存/FD/资源限制、非 root 执行 —— `design.md:97` 将 V1-local 机制定为 exported-workspace + path-guard（`GEMINI_SANDBOX=false`），容器为可选 deploy-time flag；本轮 defer，留待后续切片（`-s`/`--sandbox-image`）。
- artifact 到受信任存储的 import + checksum —— 属 C14/C20（catalog: C20 owns artifact checksum mapping）；C13 只保证 workspace 隔离与清理，succeeded run 保留 workspace 供下游 promote/import。
- Vue / Workspace UI（C15）、Promote/Publish gate（C14/C16）、Git content versioning（C20）。

## 5. Acceptance

### AC1 — Deny workspace escape（game-agent-runtime spec）

**Given** runtime 输出引用绝对路径、`..` traversal、指向 workspace 外的 symlink 或受保护文件（`.git`/`.env`）
**When** adapter 扫描产物
**Then** 平台拒绝该输出，记录 sanitized policy error（`WorkspaceEscapeError`，code 保留具体原因），不 import（→ `invalid_output`）。

### AC2 — Safe cancellation and retry（run-observability spec）

**Given** 一个 active run 被 cancel、失败、超时、产 invalid output，或后端重启后 orphan
**When** run 终止 / retry
**Then** 其 partial workspace 被丢弃（`workspace_status="discarded"`，目录删除）；retry 使用新 run_id → 新 workspace，不复用旧 partial。

### AC3 — Secret redaction on raw buffers（design.md）

**Given** provider stdout/stderr 含 `sk-…`/`Bearer …`/`api-key=…`
**When** buffer 进入 diagnostics/event/artifact 扫描前
**Then** 密钥被 `[REDACTED]` 替换且不截断（stream-json 解析需完整 buffer）。

### AC4 — runtime 看不到受信任内容（design.md）

**Given** 一个真实 create run
**When** BuildService + OpenGameAdapter 执行
**Then** run 在 prepared `data/workspaces/{run_id}/{session_id}` 内执行；succeeded 时产物为该 workspace 内已校验的相对路径。

## 6. Implementation evidence (2026-08-15)

- 新增 `backend/app/agents/workspace.py`：`WorkspaceManager`（prepare/discard/discard_run）、`validate_member`（realpath + symlink + 受保护路径拒绝）、`scan_preview`（escape-safe，替代 adapter 旧 `_scan_artifacts`）、`redact_stream`（原始 buffer 脱敏，不截断）。
- 新增 `backend/app/redaction.py`：`REDACTION_PATTERNS` + `redact_text` 单一真相源；`runs.py.sanitize_text` 改为委托，避免双脱敏器分歧。
- `backend/app/agents/opengame_adapter.py`：注入 `WorkspaceManager`；`_run` 对 `process.stdout/stderr` 跑 `redact_stream` 后再喂给 mapper/`_build_result`；`_build_result` step 6 用 `scan_preview` + `validate_member`，escape → `invalid_output` 保留具体 code；删除旧 `_scan_artifacts`。
- `backend/app/services/builds.py`：`_prepare_workspace`/`_discard_workspace`；`execute_build`/`cancel_build` 在 agent.start 前 prepare；`_persist_result` 非 success 丢弃；`retry_build` 新 run_id → 新 workspace；`recover_orphaned_jobs` 丢弃 lingering `prepared` workspace。
- migration `0011_c13_workspace`：`Run.workspace_path` + `Run.workspace_status`（`prepared`/`discarded`/`imported`）。
- 测试：`test_c13_workspace.py`（path policy / 生命周期 / 脱敏 / adapter escape→invalid_output，26+ 用例，2 symlink-privilege skip on locked-down Windows）、`test_c13_build_workspace_lifecycle.py`（cancel/retry-no-partial/orphan，7 用例）、`test_c13_opengame_smoke.py`（真实 create → prepared isolated workspace，gated on creds）。
- 验证：离线全量 211 passed / 3 skipped / 0 failed；migration up/down 干净；C10 契约/fixture 测试在 C13 改动后仍绿。
- 已知限制：Windows 无 Developer Mode 时 symlink 创建被拒（WinError 1314），相关 2 个 symlink 测试 skip 并注明原因；symlink 拒绝逻辑在 POSIX CI 覆盖。
