# C15 Workspace Build Preview Design

**Date:** 2026-08-17
**Status:** Approved for implementation
**Branch:** `feature/c15-workspace-build-preview`

## Goal

把 C10/C12/C14 已经持久化的真实 Build、Candidate、Human Play Review 和 Playable Version 状态接入现有 K02 Workspace，使用户可以完成：

```text
Build
→ Candidate Ready
→ 平台验证
→ Human Play Review
→ Promote
→ 真实 Playable Preview
```

刷新、重连、失败、取消和重试都不得重复启动 Build 或改变当前 Playable。

## Existing Context

- `frontend/src/stores/projectStore.ts` 已有真实 Build 创建、轮询、取消、Candidate Test 和 localStorage 恢复逻辑。
- `frontend/src/screens/K02ProjectWorkspace.vue` 已有 Build Timeline、Candidate Ready 和静态 Preview 视图。
- C14 后端已有 Candidate Test、Human Play Review、Promote 和 Playable Version service/API，但前端只接到了 Candidate Test。
- OpenGame 成功产物位于 C13 run workspace，API 当前只返回相对 `artifact_path`，没有安全的 HTML Preview 读取入口。

## Decisions

### 1. 复用现有 Workspace 和 store

不新增路由、Pinia 或第二套 Workspace。`ProjectSession.remoteBuild` 继续作为页面运行态入口，新增字段仅描述后端已经拥有的 Human Review、Playable 和 Preview 元数据。

`projectStore` 负责业务状态变更和 API 调用；K02 只负责局部 tab、modal 和 loading 状态。

### 2. 真实状态恢复优先于 local fixture

打开或刷新 Project 时：

1. 读取 Project summary；
2. 读取最新 Build；
3. 若存在 Candidate，读取其 TestReport 和 Human Play Review；
4. 若存在 current Playable，读取 Playable Version 并恢复 Preview；
5. 只有 confirmed GameSpec 且没有任何可恢复 Build/Playable 状态时，才创建新的 Build。

终态 Build 不得因为页面刷新再次调用 `POST /builds`。

### 3. Human Gate 是独立动作

Candidate Test 通过只把 Candidate 标记为 ready，不自动 Promote。

用户在 Workspace 中明确点击“接受并设为 Playable”后，前端调用 Human Play Review，再调用 Promote。任何失败都保留 Candidate 和错误状态，不改变 current Playable。

第一版提供：

- 接受并设为 Playable
- 拒绝并重新构建

拒绝不删除原 Candidate，重建继续使用后端 retry/repair ancestry。

### 4. Preview 使用真实 artifact

后端增加只读 Preview endpoint，依据 `project_id`、`version_id` 找到 Playable 对应 Candidate 的 Build/Run workspace，并通过现有 workspace path policy 校验 `artifact_path` 后返回 `FileResponse`。

安全约束：

- 只允许当前 Project 的 Playable Version；
- 只允许已验证的 `index.html` 入口；
- 拒绝绝对路径、`..`、symlink escape 和 workspace 外文件；
- 不允许通过 Preview endpoint 读取 `.env`、源码凭据或其他 workspace 文件；
- 找不到 artifact 返回结构化 404/409，不返回服务器路径。

前端使用同源 iframe URL 展示真实 HTML；没有 Preview URL 时保留现有轻量空态，不伪造“已可试玩”。

### 5. Failure and retry behavior

- `running` / `pending`：显示构建中，允许取消；刷新只恢复状态。
- `succeeded` + Candidate：显示 Candidate Ready，等待平台验证/Human Gate。
- `failed` / `cancelled` / `timed_out` / `invalid_output`：显示失败原因和重试入口，current Playable 不变。
- Candidate Test 未通过：显示平台证据和重新构建入口，current Playable 不变。
- Promote 成功：切换到 Playable Preview，记录 version id；不依赖本地 fixture 生成新的版本。

## Data Flow

```text
K02 confirm GameSpec
  → projectStore.startRemoteBuild
  → POST /projects/{id}/builds
  → GET /builds/{build_id} (poll)
  → Candidate Ready
  → POST /candidates/{id}/test
  → Human Review modal
  → POST /candidates/{id}/human-play-review
  → POST /candidates/{id}/promote
  → GET /projects/{id}/playable-versions
  → iframe /api/v1/projects/{id}/playable-versions/{version_id}/preview
```

## Files in Scope

### Backend

- `backend/app/api/playables.py`: Preview endpoint and response/error handling。
- `backend/app/api/projects.py` or a small shared query helper: expose latest Candidate review state needed for refresh。
- `backend/tests/test_c15_preview_api.py`: path safety, current-project ownership, missing artifact and successful HTML response。

### Frontend

- `frontend/src/api/client.ts`: Human Review, Promote, Playable Version and Preview API types/functions。
- `frontend/src/stores/projectStore.ts`: remote review/playable state, refresh hydration, Human Gate actions, preview URL。
- `frontend/src/screens/K02ProjectWorkspace.vue`: Candidate review actions, loading/error states and Playable transition。
- `frontend/src/components/workspace/BuildPreview.vue` or a focused child: real iframe preview with static fallback only when no real URL exists。
- `frontend/src/components/workspace/BuildCoworkPanel.vue` / `BuildWorkspaceView.vue`: copy and state labels for Human Review/Promote。
- `frontend/tests` or existing frontend test location: store/client behavior tests if the project already has a configured runner; otherwise rely on `vue-tsc`, build and browser acceptance.

## Non-Goals

- No Vue Router, Pinia, backend worker, queue or new runtime dependency。
- No Release Publish implementation beyond preserving the existing UI entry point。
- No Change workflow implementation。
- No artifact import/copy into frontend static assets。
- No automatic Promote or automatic Human Review decision。

## Acceptance Criteria

1. A real successful Build returns Candidate Ready in Workspace.
2. Refresh during Build does not create a second Build.
3. Candidate Test evidence is visible and a failed gate cannot be promoted.
4. Accepted Human Review followed by Promote creates the current Playable Version.
5. The Workspace Preview loads the promoted run's real `index.html` through a safe endpoint.
6. Refresh after Promote restores the same Playable and Preview URL.
7. Failure, timeout, cancellation and retry preserve the previous current Playable.
8. Backend tests cover ownership/path safety and frontend build/typecheck pass.
