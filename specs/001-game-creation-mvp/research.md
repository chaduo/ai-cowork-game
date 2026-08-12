# Phase 0 Research: AI 游戏共创平台 V1/V2

**Date（日期）**: 2026-08-07
**Spec（规格）**: [spec.md](spec.md)
**Planning constraint（规划约束）**: 两名开发者，必须在 2026-08-19 前完成在线演示

## 1. 前端基线

**Decision（决策）**: 前端固定采用 Vue 3.5、TypeScript 5.9、Vite 7.3 和 Monaco Editor 0.55。
运行环境使用 Node.js 22 LTS。生产依赖只保留 Vue 与 Monaco；使用 Vue composables、浏览器
原生 `fetch` 和 `EventSource`，不引入 React、Pinia、Axios 或组件框架。构建依次执行
`vue-tsc --noEmit` 与 `vite build`。

**Rationale（理由）**: Vue 官方推荐 Vite 与 `vue-tsc` 的 TypeScript 工作流。固定成熟主版本可减少
结项前的工具链变化；当前页面规模不需要额外状态管理和请求抽象。

**Alternatives considered（考虑过的替代方案）**:

- React：用户明确排除。
- Vite 8：当前 MVP 不需要在交付前切换构建核心。
- Pinia、Axios、UI 框架：增加依赖但不直接提升核心闭环。

**Sources（资料来源）**: [Vue TypeScript guide](https://vuejs.org/guide/typescript/overview),
[Vite releases](https://vite.dev/releases),
[Node.js releases](https://nodejs.org/en/about/previous-releases),
[Monaco Editor](https://microsoft.github.io/monaco-editor/)

## 2. 后端基线

**Decision（决策）**: 后端固定采用 Python 3.11+ 与 FastAPI。SQLite 直接使用 Python 标准库
`sqlite3` 和显式 SQL repository，不引入 SQLAlchemy、SQLModel 或 Alembic。数据库初始化
与升级使用少量顺序 SQL 文件。测试使用 pytest 与 FastAPI 测试客户端。

**Rationale（理由）**: 必要元数据只有项目、run、版本、消息和路径，标准库已足够。FastAPI 同时支持
REST、流式响应、Pydantic 输入校验和 OpenAPI，可避免 Node 后端与额外数据访问层。

**Alternatives considered（考虑过的替代方案）**:

- Fastify 或其他 Node.js 后端：用户明确排除。
- ORM 与完整迁移框架：对单用户、单项目 SQLite 数据量没有收益。
- 独立 worker 服务：会增加部署和调试面。

**Sources（资料来源）**: [FastAPI documentation](https://fastapi.tiangolo.com/),
[FastAPI version pinning](https://fastapi.tiangolo.com/deployment/versions/),
[Python sqlite3](https://docs.python.org/3.11/library/sqlite3.html)

## 3. 模块化单体与目录

**Decision（决策）**: 仓库只保留 `frontend/`、`backend/`、`game-template/` 和 `deploy/` 四个主要模块。
单个 FastAPI 应用承载 REST、SSE、任务启动、SQLite、Git 版本管理和游戏静态产物发布；Vue
构建为静态管理页面。运行数据使用以下简单目录：

```text
data/
├── app.db
├── projects/{project_id}/repo/
├── workspaces/{run_id}/{agent_session_id}/
├── candidates/{project_id}/{candidate_id}/
├── test-reports/{candidate_id}/{attempt}.json
├── artifacts/{project_id}/{version_number}/
└── logs/{run_id}/build.log
```

**Rationale（理由）**: 结构与团队分工清晰，同时只有一个后台应用和一个数据库。项目源码、素材和
GameSpec 都在同一 Git 仓库内，直接满足 AI 与用户编辑同一项目。

**Alternatives considered（考虑过的替代方案）**: 微服务、共享 packages 层、对象存储和分布式文件系统均不进入 MVP。

## 4. SQLite 与 Git 版本

**Decision（决策）**: SQLite 保存项目、run、Agent session、Candidate、TestReport、Version、消息和
文件路径。每次变更先创建 Candidate；只有构建成功且有效 TestReport 为 PASS 时才导入可信 Git
仓库并创建不可变 Version。项目保留最新 Candidate 和 `playable_version_id` 指针。构建产物
保存在普通版本目录，不使用内容寻址或对象存储。

MVP 仅按结项演示所需的少量版本设计，预计不超过 10 个；不实现自动归档、垃圾回收或大规模
历史优化。

**Rationale（理由）**: Git 已提供快照、差异和恢复。普通路径配合 SQLite 指针即可保证失败 Candidate 不会
替换最近成功版本，不需要第三套存储抽象。

**Alternatives considered（考虑过的替代方案）**: SHA 内容寻址、Git worktree 编排、100 个版本容量设计和复杂保留
策略均被移除。

**Sources（资料来源）**: [Git commits](https://git-scm.com/docs/git-commit),
[SQLite transactions](https://www.sqlite.org/lang_transaction.html)

## 5. 单任务执行与 SSE

**Decision（决策）**: 全平台同一时间只允许一个活动任务。FastAPI 进程使用单个任务锁和 SQLite
`active_run_id` 条件更新；第二个请求返回 `409 task_running`，不排队。run 消息先写 SQLite，
再通过 FastAPI SSE 响应推送；每条消息只包含 sequence、run ID、stage、type、level、message、
timestamp 和可选 progress。浏览器使用 `Last-Event-ID` 补发少量遗漏消息。

**Rationale（理由）**: 单用户、单项目无需 Redis、Celery、RQ 或消息代理。SSE 正好覆盖服务器到浏览器
的单向阶段和日志流。

**Alternatives considered（考虑过的替代方案）**: WebSocket、消息队列、多个 worker 和分布式锁均被移除。

**Sources（资料来源）**: [FastAPI streaming](https://fastapi.tiangolo.com/advanced/stream-data/),
[Server-Sent Events](https://html.spec.whatwg.org/dev/server-sent-events.html)

## 6. Agent Runtime Roadmap

**Decision（决策）**: 采用 V1/V2 分阶段 Runtime Roadmap。稳定平台边界继续命名为
`GameAgentAdapter`。V1 使用 `OpenGameAdapter` 建立
GameSpec → Coding → Candidate → Build → Test → Version baseline。V2 使用 Claude Agent SDK
实现 `ClaudeRuntimeAdapter`，由 FastAPI 顺序编排 PlanningAgent、AssetAgent、CodingAgent
和 TestAgent，并成为主要后端。OpenGame 在 V2 保留为 fallback/reference/benchmark。

**Rationale（理由）**: V1 先验证平台与 Phaser 领域能力，避免在核心契约未知时直接构建复杂 Runtime；
V2 复用相同 Workspace、GameSpec、Candidate、TestReport、Version 和 RunEvent 契约，最终形成平台
自己的领域 Agent 能力。FastAPI 控制业务阶段，避免 LLM 自由决定确认和发布。

**Alternatives considered（考虑过的替代方案）**: 只交付 OpenGame、把 Claude 模型接入 OpenGame、让 LLM
自由创建/编排 Agent、把四个 Agent 拆为微服务均被拒绝。

**Sources（资料来源）**: [Python asyncio subprocess](https://docs.python.org/3.11/library/asyncio-subprocess.html),
[OpenGame repository](https://github.com/leigest519/OpenGame),
[Claude Agent SDK Python](https://github.com/anthropics/claude-agent-sdk-python)

## 6.1 Claude Runtime 权限与事件边界

**Decision（决策）**: V2 使用 `ClaudeSDKClient` 承载需要流式事件、取消和自定义 MCP 工具的受控
session；一次性无工具规划可以使用 `query()`，但仍经同一 Adapter 规范化。四类 Agent 使用独立
system instructions、Domain Skills、工具策略和 Workspace 权限。平台持久化 run ↔ AgentSession ↔
Candidate/TestReport 映射，并将 Claude 原生 message/content block/result 转换为供应商无关
RunEvent。自定义平台工具优先使用进程内 SDK MCP server；外部 MCP 只通过平台批准 gateway 注册，
业务状态写操作不作为 Agent 工具暴露。

SDK 的 `allowed_tools` 表示自动批准列表，并不会移除其他内置工具，因此不能单独作为安全边界。
每个 profile 必须同时配置 `disallowed_tools`、`can_use_tool` 或 `PreToolUse` 拒绝逻辑，并依赖 Docker
挂载和路径白名单形成最终边界。FastAPI 使用 SDK session ID 映射平台 `agent_session_id`；SDK 的
resume 能力不改变本项目“从最近成功 Version 新建 run”的产品恢复语义。

**Rationale（理由）**: 独立 profile/session 能建立最小权限和可追溯性，同时保持模块化单体部署。
规范化事件使前端和数据模型不被 SDK 原生事件格式锁定。

**Alternatives considered（考虑过的替代方案）**: 单个无限权限通用 Agent、前端直接消费 Claude event、
Agent 直接写数据库状态和常驻 Agent 服务均被拒绝。

**Sources（资料来源）**: [Claude Agent SDK Python README](https://github.com/anthropics/claude-agent-sdk-python),
[ClaudeSDKClient source](https://github.com/anthropics/claude-agent-sdk-python/blob/main/src/claude_agent_sdk/client.py),
[ClaudeAgentOptions types](https://github.com/anthropics/claude-agent-sdk-python/blob/main/src/claude_agent_sdk/types.py)

## 6.2 可复用开发知识

**Decision（决策）**: V2 使用 SQLite 元数据和 `data/resources/` 普通目录实现小型人工审核资源目录，
只包含 `ReusableTemplate`、`DevelopmentExperience`、`ReusableAsset`、`ResourceUse` 和可选
`SkillCandidate`。Template 由成功 Version 手工晋升并按固定 `phaser-survival-v1` capability tag
匹配；Asset 必须先通过 Asset Accept；Experience 必须引用成功 run、来源 Version/Candidate 和
PASS TestReport，并经人工审阅变为 `available`。CodingAgent 只能使用平台只读工具按精确标签获取
少量兼容 Experience。

产品仍只维护一个活动项目。跨项目复用验收通过“归档项目 A → 顺序创建隔离项目 B → 平台复制
已批准资源并记录 ResourceUse”完成，不提供多项目并发界面，也不把来源 Workspace 暴露给目标
Agent。单次成功 Run 最多产生 Skill Candidate，Formal Skill 必须另行审阅和验证。

**Rationale（理由）**: 结构化记录、精确标签和人工门禁足以证明成功工程知识能够积累和复用，
同时可直接验证证据链、隔离和兼容性。它不需要向量数据库、embedding pipeline、聚类任务或动态
Skill loader，适合两人团队的结项期限。

**Alternatives considered（考虑过的替代方案）**: 自动从 Version 提取模板、向量相似度检索、自动
经验聚类、单次成功即更新 Skill、共享来源项目目录和资源市场均被移除，作为结项后 stretch goal。

## 7. 失败恢复与取消

**Decision（决策）**: 不实现通用阶段检查点。失败任务的 retry/resume 从最近成功 Version 重跑；
Test FAIL 可在同一变更链路内创建新的 repair Candidate attempt，并由 TestAgent 重新测试。repair
次数、时间和成本由 FastAPI 限制。用户恢复历史 Version 时先创建 Candidate，重新验证通过后发布
新 Version，不改写 Git 历史。

**Rationale（理由）**: 从已验证 commit 重跑具备明确、可测试的恢复语义，且不会依赖 OpenGame 中间
状态。它满足结项演示需要，并删除阶段检查点和部分工作区恢复；只有明确受预算限制的
Candidate repair attempt 保留。

**Alternatives considered（考虑过的替代方案）**: 原地续跑、阶段重放和工具调用级恢复均被移除。

## 8. Docker 隔离与编辑白名单

**Decision（决策）**: OpenGame、文件修改、npm 安装、生产构建和 Playwright 冒烟测试都在当前 run 的
Docker 工作区执行。容器只挂载该 run workspace，以非 root 用户运行，并限制 CPU、内存、
PID、时间与输出；不得挂载用户主目录、平台源码、其他项目、宿主凭证或可信 Git 仓库。

Monaco 只能保存 GameSpec、NPC 配置和 `game-template` 规定的源码白名单。后端对规范化路径
再次校验，拒绝绝对路径、`..`、符号链接逃逸和受保护文件。界面不提供终端或任意命令入口。

**Rationale（理由）**: 这是满足 Constitution 安全边界的最小实现。白名单既保护模板和平台，又能完成
直接修改源码的演示。

**Alternatives considered（考虑过的替代方案）**: 宿主直接执行、在线终端、完整 IDE、任意文件编辑和 Kubernetes
sandbox 均被移除。

**Sources（资料来源）**: [Docker run](https://docs.docker.com/reference/cli/docker/container/run),
[Docker resource constraints](https://docs.docker.com/engine/containers/resource_constraints/)

## 9. 固定 Phaser 模板、素材与验证

**Decision（决策）**: 游戏固定使用 Phaser 3.90、TypeScript、Vite 7 与 Arcade Physics，包含玩家移动、
敌人生成与追踪、生命值、道具、计分、胜负条件，以及 `idle | patrol | flee` 确定性 NPC。
GameSpec 使用 JSON Schema 与 Ajv 校验。素材优先调用批准的生成/接入能力；失败时复制模板内置
角色、敌人、道具、背景和 NPC 占位素材，并记录 `builtin_placeholder` 来源，继续构建。

每个 Candidate 执行依赖准备、类型检查、生产构建和一个 Chromium Playwright playtest。结构化
TestReport 必须覆盖页面/canvas 启动、无阻断错误、玩家移动、敌人循环、道具收集、NPC 对话和
至少一个胜负条件。平台验证必需项、证据和真实退出码后，才发布 Version 并更新
`playable_version_id`。

**Rationale（理由）**: 单模板、占位素材和单浏览器测试直接保护演示闭环，避免外部素材或跨浏览器矩阵
阻断结项。

**Alternatives considered（考虑过的替代方案）**: Phaser 4、多模板、实时 LLM NPC、三浏览器自动化、视觉回归和完整
动画/音乐生成均被移除。

**Sources（资料来源）**: [Phaser 3](https://phaser.io/download/phaser3),
[Phaser physics](https://docs.phaser.io/phaser/concepts/physics),
[Playwright Chromium](https://playwright.dev/docs/browsers)

## 10. 单机部署与交付

**Decision（决策）**: 在线环境是一台 Linux 主机和一个 Docker Compose 项目，包含反向代理、FastAPI
应用与受限运行容器能力；Vue 构建静态文件由同一部署提供。SQLite、项目目录、构建产物、日志
和演示视频放在持久卷。只提供基本 HTTP 健康检查、容器日志轮转、部署/重启/演示重置步骤。

管理页面使用一个环境变量配置的部署级访问码，不实现账号、RBAC 或用户数据库。演示前锁定
Python/npm/OpenGame/容器版本，预置占位素材和一个成功游戏，并完成录屏。

**Rationale（理由）**: 单机 Compose 是满足公开访问、Docker 构建与两人维护能力的最短路径。

**Alternatives considered（考虑过的替代方案）**: Kubernetes、微服务、云数据库、复杂备份系统、完整监控、弹性扩容
和多节点高可用均被移除。

**Sources（资料来源）**: [Docker Compose production](https://docs.docker.com/compose/how-tos/production/)

## Resolved Unknowns（已解决的不确定项）

技术栈、目录、持久化、单工作流、V1/V2 Runtime 边界、Candidate/Version、事件规范化、恢复、
隔离、素材回退、人工审核资源复用、验证和部署方向均已确定。Claude Agent SDK 的精确固定版本和真实 OpenGame CLI
参数属于实现前 spike 的版本锁定事项，不改变本设计。React、Fastify、Node.js 后端、通用阶段
检查点、内容寻址、大规模容量、向量检索、经验聚类、自动 Skill 晋升、三浏览器测试、Agent
微服务和复杂运维设计均不属于本计划。
