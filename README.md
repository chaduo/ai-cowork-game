# AI Cowork Game

AI Cowork Game 是一个面向创作者的 AI 游戏协作原型：用户从 Idea 开始，经过 Game Design、GameSpec、Build、Playable、Change、Version、Publish，再沉淀 Resource Review 和跨项目资源复用。

当前仓库包含两部分：

- `frontend/`：Vue 3 + TypeScript + Vite 的产品原型。
- `test/agent-game-forge/`：独立的 OpenGame / Agent Game Forge 工具仓库，以 Git submodule 方式接入。它不是主项目的普通源码目录，也不在主仓库内复制维护。

## 快速开始

要求 Node.js 20+ 和 npm。

```bash
git clone <主仓库地址>
cd ai-cowork-game
git submodule update --init --recursive
cd frontend
npm ci
npm run dev
```

打开 Vite 输出的本地地址即可查看原型。生产构建和类型检查：

```bash
cd frontend
npx vue-tsc -b
npm run build
```

## OpenGame 子模块

本项目当前使用的子模块路径是 `test/agent-game-forge`。它对应独立仓库：

<https://github.com/0x0funky/agent-game-forge>

第一次克隆主仓库后必须初始化子模块：

```bash
git submodule update --init --recursive
```

进入子模块开发时，先在子模块自己的目录内创建 branch、提交和推送；主仓库只提交子模块指针变化。子模块的依赖安装、运行命令和发布方式以它自己的 `README.md` 为准。

## 文档入口

- [`docs/development/V1_CHANGE_CATALOG.md`](docs/development/V1_CHANGE_CATALOG.md)：C00-C19 的范围、依赖和 OpenSpec Explore 输入。
- [`docs/development/V1_DEMO_IMPLEMENTATION_SCHEDULE_2026-08-20.md`](docs/development/V1_DEMO_IMPLEMENTATION_SCHEDULE_2026-08-20.md)：8 月 20 日展示倒排计划。
- [`docs/development/DAILY_DEVELOPMENT_CHECKLIST.md`](docs/development/DAILY_DEVELOPMENT_CHECKLIST.md)：每天开工、验证、Review、合并和日终 Gate。
- [`docs/development/GIT_BRANCH_PR_WORKFLOW.md`](docs/development/GIT_BRANCH_PR_WORKFLOW.md)：branch、PR 和合并约定。
- [`docs/development/OPENSPEC_SUPERPOWERS_WORKFLOW.md`](docs/development/OPENSPEC_SUPERPOWERS_WORKFLOW.md)：OpenSpec 与 Superpowers 的协作方式。
- [`openspec/`](openspec/)：当前 Change 的 proposal、design、spec 和 tasks。

## 协作原则

一个 Change 对应一个 Owner、一个 feature branch 和一个 PR。业务生命周期的状态变更必须经过项目状态层；前端不绕过 Human Gate 推进状态。真实 OpenGame 验收与 Fake contract test 分开记录，不能用 demo fixture 冒充端到端 evidence。

详见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。
