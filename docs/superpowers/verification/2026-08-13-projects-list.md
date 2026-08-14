# C04 Projects List Verification

## Scope

- Projects 页面使用真实 `GET /api/v1/projects` 数据，不再依赖预置项目 fixture。
- Project 列表和详情返回同一份生命周期摘要：派生 stage、updatedAt、current playable、latest release。
- 刷新后用持久化 Project 记录恢复最小 Workspace 会话；内存已有会话继续复用，避免跨项目状态污染。
- 覆盖空列表、加载失败和项目不存在状态。

## Implementation

- `backend/app/api/projects.py`
  - 扩展 Project response 的 `updated_at`、`current_playable`、`latest_release`。
  - 摘要从 ProjectLifecycleService 和持久化 PlayableVersion/Release 查询得到。
- `backend/tests/test_c04_projects_list.py`
  - 空列表、多个项目状态隔离、发布摘要和不存在项目错误 envelope。
- `frontend/src/api/client.ts`
  - 对齐 Project 摘要类型。
- `frontend/src/App.vue`
  - 加载真实项目列表、恢复最小 session、按稳定 project id 打开项目、处理列表/详情异常。
- `frontend/src/screens/K01CreateProject.vue`
  - 展示远端项目、后端派生 stage、加载/错误/空态。
- `frontend/src/style.css`
  - 增加项目列表状态样式，保持现有视觉语言。

## Verification

```text
backend/.venv/bin/pytest backend/tests -q
27 passed, 1 warning

cd frontend && npx --no-install vue-tsc -b && npx --no-install vite build
vite v6.0.5 ... built in 3.31s
```

The first frontend command attempted to download dependencies because the new worktree had no local `node_modules`; network resolution was unavailable. Re-running with the existing C03 worktree dependency tree passed typecheck and build without changing package metadata.
