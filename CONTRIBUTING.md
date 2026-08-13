# Contributing

## 开始工作

```bash
git switch main
git pull --ff-only
git submodule update --init --recursive
```

每个 Change 使用独立 branch：

```bash
git switch -c feature/cxx-change-name
```

先阅读 [`docs/develop/V1_CHANGE_CATALOG.md`](docs/develop/V1_CHANGE_CATALOG.md) 和当天的 [`docs/develop/V1_DEMO_IMPLEMENTATION_SCHEDULE_2026-08-20.md`](docs/develop/V1_DEMO_IMPLEMENTATION_SCHEDULE_2026-08-20.md)，再按 [`docs/develop/DAILY_DEVELOPMENT_CHECKLIST.md`](docs/develop/DAILY_DEVELOPMENT_CHECKLIST.md) 开工。

## 前端验证

```bash
cd frontend
npm ci
npx vue-tsc -b
npm run build
```

提交前确认 `git status --short` 中没有 `node_modules`、`dist`、`.tsbuildinfo`、`.DS_Store`、压缩包、数据库或密钥。

## Submodule 规则

`test/agent-game-forge` 是独立仓库。修改它时：

1. 在 `test/agent-game-forge` 内创建 branch 并完成它自己的测试与提交。
2. 推送子模块仓库后，在主仓库更新 submodule pointer。
3. 主仓库 PR 中说明对应的子模块 commit 和兼容性影响。

不要把子模块目录转成普通文件夹，也不要在主仓库复制一份 OpenGame 源码。

## Pull Request

PR 标题包含 Change ID，例如：

```text
[C07] feat(build): persist build candidates
```

PR 说明至少包含：Change/OpenSpec 路径、完成内容、Out of Scope、验收证据、测试命令和 Reviewer 重点。Required Reviewer 批准、验证通过且无冲突后再合并。

