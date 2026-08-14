# C11 Build Job Orchestration Design

## Goal

通过 C06 的 provider-neutral GameAgent contract 管理 Build 与 Run，从已确认的 CreatorGameSpec 创建 BuildCandidate；不触碰 Promote、TestReport 或 Workspace UI。

## Decisions

1. `BuildService` 是唯一编排边界。它只依赖 `GameAgent`、`RunRepository` 与既有 Project lifecycle service，不知道 OpenGame 命令、子进程或日志格式。
2. 创建 Build 时把 confirmed GameSpec revision、baseline playable pointer、operation 和 request text 固定在 Build record 上。后续执行不会重新选择 GameSpec，也不会读取执行期间变化的 current playable。
3. 每个 Build 都有稳定的 `build_id` 与 `run_id`。重复请求带同一 id 返回已存在 job；同一 Project 只有一个 active Build。重试创建新的 Build，保留 `parent_build_id` 和递增 attempt。
4. FakeGameAgent 通过 C06 contract 驱动事件和结果。BuildService 持久化非终态事件，再由 `GameBuildResult` 统一决定 Run/Build 终态；provider event 不会直接修改 current playable 或 Release。
5. 成功结果创建 `BuildCandidate`，但不 Promote。失败、取消、timeout、invalid output、unsupported 的 diagnostics 保留在 Build/Candidate，并且不修改 current playable。
6. 后端重启恢复时，活动 Run 标记为 orphaned，相关 Build 结束为 orphaned 并释放 active guard；不会伪造成功，也不会永久停留在 running。

## API Surface

- `POST /api/v1/projects/{project_id}/builds`
- `GET /api/v1/builds/{build_id}`
- `POST /api/v1/builds/{build_id}/cancel`
- `POST /api/v1/builds/{build_id}/retry`

API 只返回 Build/Run/Candidate 的状态摘要。C11 不增加前端 Workspace 行为。

## Data and Failure Rules

- Build input fields are immutable after creation.
- `succeeded` creates one candidate for the Build; no current playable pointer is set.
- Non-success results keep sanitized diagnostics and failure code/message.
- Cancel is idempotent for terminal jobs. Retry is allowed only from failed/cancelled/orphaned jobs and is guarded by the same active-build rule.
- Agent start/stream/result exceptions become a failed Run/Build with sanitized diagnostics.

## Test Strategy

Service tests cover confirmed-input capture, idempotency, active-build guard, success/failure/cancel/retry, current-playable immutability, and orphan recovery. API tests cover create/query/cancel/retry contracts. Existing C02/C06/C07 tests remain green.
