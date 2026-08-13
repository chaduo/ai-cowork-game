# AI Cowork Game V1 Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 2026 年 8 月 20 日前完成 C00-C19 的真实 V1 闭环，并稳定展示两个 Project、OpenGame Build、Candidate/Test/Promote、Playable、Release、Resource Review、我的资源和跨项目复用。

**Architecture:** zhao 负责产品状态机、FastAPI、持久化、Vue 和全部 Human Gate；zhang 负责 OpenGame CLI、Executor、Adapter、事件映射和运行隔离。双方先冻结 provider-neutral contracts，再使用 FakeGameAgent 与真实 OpenGame 双轨开发，每天将一个新的真实纵向切片合并到 `main`。

**Tech Stack:** Vue 3、TypeScript、Vite、Python 3.11+、FastAPI、SQLite、OpenGame CLI、REST、SSE、浏览器 E2E。

## Global Constraints

- 展示日：2026-08-20；2026-08-19 12:00 后功能冻结。
- zhao 与 zhang 每天基线投入各 6 小时；日终 Gate 未通过时，当晚各最多增加 2 小时追回当天 Gate。
- C00-C19 全部接真实后端、持久化和 OpenGame；FakeGameAgent 只用于 contract tests，不能用于最终 E2E 或展示结果。
- FastAPI 是业务状态和 Human Gate 的唯一 Owner；Vue 不自行推进业务状态。
- `BuildCandidate → TestReport PASS → Human Promote → PlayableVersion → Human Publish → Release` 不得简化。
- `BuildCandidate` 与 `ResourceCandidate` 必须使用不同 schema、API 和 repository。
- 一个 Change 一个 Owner、一个 feature branch、一个 PR；Required Reviewer 未批准不得合并。
- 不引入 V2 自研 Agent、Marketplace、多用户、团队权限、分布式 worker 或通用 workflow engine。
- 每天 17:00 前必须合并或明确回滚当天纵向切片，不把未集成分支拖到下一天。
- 任何 contract 变化先更新 OpenSpec，再改代码。

---

## 1. 时间预算与工作节奏

### 总预算

```text
8 月 13–19 日：7 天 × 2 人 × 6 小时 = 84 人时
8 月 15 日 zhao 计划内加时：2 人时
条件加时上限：4 个晚上 × 2 人 × 2 小时 = 16 人时
可用实现预算：86–102 人时
8 月 20 日：展示、健康检查和阻塞性修复，不计入功能实现预算
```

### 每日固定节奏

```text
09:30–09:50  同步 main、确认当天 Gate、确认 contract/文件所有权
09:50–12:30  上午专注块
14:00–16:20  下午专注块
16:20–17:00  交叉 Review、合并、真实纵向验收、记录 evidence
19:30–21:30  仅在 Gate 未通过时启动；禁止用于提前做明日功能
```

每日结束必须记录：

- 已合并的 Change/PR/commit。
- 当天 Gate 的真实命令、API 响应、artifact 或浏览器 evidence。
- Contract 是否变化。
- 未关闭 blocker 和第二天第一处理人。

---

## 2. 开工 Gate

2026-08-13 10:00 前完成：

- [ ] zhao：确认 `feature/project-lifecycle-store` 已 Review 并合并到 `main`，或明确标记为只读 Prototype reference。
- [ ] zhang：从同一个最新 `main` 开始 C08，不从独立旧副本或嵌套 test repository 开发产品实现。
- [ ] 双方：确认 `docs/development/V1_CHANGE_CATALOG.md` 为 roadmap 输入，C00 完成后 OpenSpec 才成为 contract 事实源。
- [ ] 双方：建立共享的 PR/CI 命令清单和本地 secret 配置方式，禁止提交 OpenGame credential。

Gate 失败时，C01-C19 不开工。

---

## 3. 逐日执行计划

### 8 月 13 日（周四）：C00 Contract Alignment + C08 OpenGame CLI Spike

**当日目标：** 冻结术语、V1 范围、Human Gate 和 OpenGame 真实能力，消除后续并行开发的解释空间。

#### zhao — C00 `v1-contract-alignment`（6h）

**上午 09:50–12:30**

- [ ] 使用 Catalog 第 8.1 节执行 OpenSpec Explore，生成 glossary、生命周期、CreatorGameSpec/RuntimeBuildSpec 边界和旧 artifact 迁移矩阵。
- [ ] 冻结 `BuildCandidate`、`TestReport`、`PlayableVersion`、`Release`、`ResourceCandidate`、`SavedResource` 的职责和 ID/provenance 关系。
- [ ] 决定现有 `platform-v1-opengame-baseline` 是更新、split、sync 还是 archive，禁止保留第二套实现事实源。

**下午 14:00–16:20**

- [ ] 更新 `openspec/config.yaml` 的多项目 V1 范围和 Human Promote/Publish 规则。
- [ ] 更新或替换旧 GameSpec/OpenAPI/data-model contract，建立逐文件迁移清单。
- [ ] 创建/更新 C00 OpenSpec artifacts，并完成 self-review：无自动 Promote、无 Candidate/ResourceCandidate 混名、无固定 survival 与 Prototype 范围冲突。

#### zhang — C08 `opengame-cli-spike`（6h）

**上午 09:50–12:30**

- [ ] 固定 OpenGame 版本、安装命令、非交互 create 命令、cwd/env 输入和真实退出码。
- [ ] 完成一次真实生成，保存 sanitized stdout/stderr、output tree 和真实 `index.html` 路径 evidence。
- [ ] 验证缺少输入、非法输入和非零退出码。

**下午 14:00–16:20**

- [ ] 验证 timeout、cancel、child process、incremental modify；不支持的能力明确标为 unsupported。
- [ ] 保存 create/success/failure/cancel/invalid-output fixtures，供 C09/C10 contract tests 使用。
- [ ] 提交 C08 spike report，列出 C06 contract 必须表达的字段。

#### 16:20–17:00 共同 Gate

- [ ] zhang Required Review C00；zhao Required Review C08。
- [ ] 合并 C00 与 C08。
- [ ] 双方口头复述同一生命周期和 GameAgent 边界，结果必须一致。

**日终验收：** C00、C08 Done；真实 OpenGame 命令可重复产生 `index.html`；旧事实源有单一迁移处置。

**加时触发：** 16:20 时 Human Gate、GameSpec boundary 或 CLI invocation 任一未冻结，双方 19:30–21:30 只处理该 blocker。

---

### 8 月 14 日（周五）：C01 Backend Foundation + C02 Domain + C09 Executor

**当日目标：** 后端可启动、migration 可重复执行、核心领域可持久化、Executor 可可靠运行固定 OpenGame。

#### zhao — C01 `platform-backend-foundation`（2.5h）

- [ ] 创建 FastAPI application、配置、SQLite connection/migration、transaction 和测试数据库隔离。
- [ ] 添加 health endpoint、统一 error envelope 和 API test harness。
- [ ] 运行 migration 两次，证明幂等；运行 health/error tests。
- [ ] C01 PR Review/merge 后立即开始 C02，不在同一 PR 混入领域表。

#### zhao — C02 `project-lifecycle-domain`（3.5h）

- [ ] 先写 repository/service tests：Candidate success/failure 不改 current Playable，Promote/Publish 尚不可由 Agent 调用。
- [ ] 创建 Project、GameDesignRevision、GameSpecRevision、Build、BuildCandidate、TestReport、PlayableVersion、Release 的最小 schema/repository。
- [ ] 实现 Project stage 派生、active build guard、updatedAt 和 orphaned build recovery 基础。
- [ ] 用 SQLite integration test 证明两个 Project 状态隔离、失败不覆盖 Playable。

#### zhang — C09 `opengame-process-executor`（6h）

- [ ] 先写 executor tests：success、stderr、non-zero exit、timeout、cancel、child process、approved env。
- [ ] 实现 command/arguments/cwd/approved_env/timeout 输入和结构化 ProcessResult。
- [ ] 实现 process-tree cancellation、output limit 和 sanitized diagnostics。
- [ ] 使用 C08 的固定版本命令完成真实 Executor smoke，不接触 Project repository。

#### 日终 Gate

- [ ] `main` 可启动 FastAPI、执行 migration、运行后端 tests。
- [ ] repository test 证明 current Playable failure safety 和多项目隔离。
- [ ] Executor contract tests 和一次真实 CLI smoke 通过。
- [ ] zhang Review C01/C02；zhao Review C09。

**日终验收：** C01、C02、C09 Done。

**加时触发：** migration 不幂等、领域关系仍有重复 pointer、Executor cancel 会留下进程，任一问题未关则当晚追回。

---

### 8 月 15 日（周六）：C03 Create + C04 Projects + C05 Design/GameSpec + C06 Contract

**当日目标：** 真实持久化完成 `Idea → Project → Game Design → GameSpec Confirm`，并冻结 BuildService/Adapter 共用 contract。

**计划工时：** zhao 8h（当天计划内加时至 19:00），zhang 6h。C06 是后续真实 Build 的硬依赖，不能推迟到 8 月 16 日边集成边定义。

#### zhao — C03 `create-project-flow`（1.25h）

- [ ] 实现 create project API、Idea 校验和重复提交/idempotency rule。
- [ ] K01 改读真实 API，创建成功后打开返回的 project id。
- [ ] API/component test 证明刷新后 Original Idea 仍存在。

#### zhao — C04 `projects-list`（1.25h）

- [ ] 实现 list/get Project API 和派生 stage/current playable/latest release/updatedAt DTO。
- [ ] Projects 页面改读真实 API；覆盖 loading、empty、not-found、两个 Project 隔离。
- [ ] 删除真实入口对 `projectStore.projects` fixture 的依赖，保留 demo seed 只用于显式开发入口。

#### zhao — C05 `game-design-gamespec-flow`（3.5h）

- [ ] 实现 Game Design draft/clarification/confirm persistence 和 API。
- [ ] 冻结并校验 CreatorGameSpec schema；实现 Prototype ViewModel ↔ API DTO mapping。
- [ ] 实现 GameSpec generation/revision/confirm；未确认或 invalid schema 拒绝 Build。
- [ ] 验证 recommended/dismissed/used/resource id/drawer state 不进入 CreatorGameSpec。

#### zhang — C10 前置 parser/mapper（4h）

- [ ] 基于 C08 fixtures 编写 output tree parser、preview entry detection 和日志/event mapping tests。
- [ ] 实现 OpenGame-private parser 模块，不导出 provider-specific 类型给上层。
- [ ] 覆盖 missing index、non-zero exit、invalid path、partial artifact。

#### 双方 — C06 `game-agent-contract`（各 2h；zhang 14:20–16:20，zhao 17:00–19:00 完成定稿）

- [ ] zhao 定义 GameBuildRequest/GameBuildResult/RunEvent/ArtifactManifest/Error contracts。
- [ ] zhang 用 C08/C10 evidence Review 所有字段是否可由真实 OpenGame 提供。
- [ ] 建立 FakeGameAgent contract suite；Fake 和 Adapter 必须共用同一 suite。
- [ ] 冻结 cancel/timeout/unsupported/invalid-output 语义。

#### 日终 Gate

- [ ] 浏览器真实创建 Project，完成 Game Design 和 GameSpec Confirm；刷新后状态恢复。
- [ ] SQLite 中存在对应 revision，不依赖 local store。
- [ ] C06 contract suite 对 FakeGameAgent 通过。
- [ ] C03、C04、C05、C06 分别 Review/merge。

**日终验收：** C03-C06 Done；C10 parser 私有部分完成但 C10 不宣称 Done。

**加时触发：** 16:20 时真实 Project/GameSpec 刷新恢复或 C06 contract suite 未通过，双方共同加时，不提前做 Build UI。

---

### 8 月 16 日（周日）：C07 Events + C10 Adapter + C11 Build + C13 Isolation

**当日目标：** 从 confirmed GameSpec 发起真实 OpenGame Build，通过 SSE 看到进度并持久化 BuildCandidate。

#### zhao — C07 `run-event-observability`（2h）

- [ ] 实现 Run/RunEvent repository、单调 sequence、status API 和 SSE replay。
- [ ] 集成 test 覆盖断线后从 last sequence 重放、刷新不创建新 run、terminal event 与 DB 一致。
- [ ] 提供 Vue API client/composable，禁止组件解析 OpenGame stdout。

#### zhao — C11 `build-job-orchestration`（4h）

- [ ] 先用 FakeGameAgent 实现 POST/query/cancel/retry Build、active build guard 和 orphan recovery。
- [ ] 固定 confirmed GameSpec、RuntimeBuildSpec 和 baseline Playable 为 Build input。
- [ ] GameBuildResult success 创建 BuildCandidate；failure/cancel 只保存 diagnostics。
- [ ] 切换到真实 OpenGameAdapter，保持同一 contract tests 不变。

#### zhang — C10 `opengame-agent-adapter`（3.5h）

- [ ] 把 C10 parser 接到 C09 Executor，实现 GameBuildRequest → OpenGame → GameBuildResult。
- [ ] 输出 ArtifactManifest、preview entry、sanitized diagnostics 和标准 RunEvent。
- [ ] 真实通过 create flow；invalid output/non-zero/timeout/cancel 返回标准失败。

#### zhang — C13 `runtime-workspace-isolation` 第一阶段（2.5h）

- [ ] 实现 per-run workspace、trusted source export、approved env/command 和输出 import allowlist。
- [ ] 增加 traversal、absolute path、symlink/protected path rejection tests。
- [ ] 确认 runtime 看不到 trusted `.git`、其他 Project 和 host credential。

#### 日终 Gate

- [ ] 浏览器从 confirmed GameSpec 发起真实 OpenGame Build。
- [ ] Workspace 经 SSE 显示真实标准事件，刷新后继续同一 run。
- [ ] 成功产生 BuildCandidate + real preview entry，但 current Playable 仍为空/保持原值。
- [ ] failure/cancel smoke 不改变 current Playable。

**日终验收：** C07、C10、C11 Done；C13 第一阶段合并。

**Stop-the-line：** 17:00 前真实 Build 未产生 BuildCandidate，则 8 月 17 日上午 zhao/zhang 全员只修 C06/C09/C10/C11 集成，C12-C15 顺延到当日下午并启用加时。

---

### 8 月 17 日（周一）：C12 Test Gate + C13 Isolation + C14 Promotion + C15 Workspace

**当日目标：** Candidate 经过真实测试和 Human Promote 成为 Playable，失败时仍可玩旧版本。

#### zhao — C12 `candidate-test-gate`（2h）

- [ ] 实现 artifact build、page load、console、核心输入/玩法/完成条件检查。
- [ ] 实现 TestReport/evidence validation；缺失、矛盾或 runtime 自报 PASS 均不可 ready。
- [ ] 实现 failed Candidate/repair ancestry，旧失败记录不可覆盖。

#### zhao — C14 `playable-version-promotion`（1.5h）

- [ ] 实现 Human Promote API、原子 PlayableVersion 创建和 current pointer 更新。
- [ ] 覆盖非 PASS 拒绝、重复 Promote 幂等和 immutable provenance。
- [ ] Restore 创建新 BuildCandidate，不 reset 版本历史。

#### zhao — C15 `workspace-build-preview`（2.5h）

- [ ] Workspace 改用真实 Build/SSE/Candidate/TestReport/Playable API。
- [ ] Candidate Preview 与 current Playable Preview 明确区分。
- [ ] 增加 Promote、failure、retry、history、restore；离开/刷新后恢复真实状态。

#### zhang — C13 完成与 C12 runtime 支持（6h）

- [ ] 完成 resource/time/output limits、network/env policy、secret redaction 和 audit evidence。
- [ ] 保证 cancel 杀掉 child process tree，retry 不复用 untrusted partial workspace。
- [ ] 为 C12 提供 deterministic test bridge/runtime hooks 和真实 artifact failure fixtures。
- [ ] Required Review C12/C14，重点检查 runtime 不能自行 Promote。

#### 日终 Gate

- [ ] 真实 Candidate PASS 后页面等待用户 Promote。
- [ ] 用户 Promote 后创建 PlayableVersion v1；刷新和返回 Projects 后仍存在。
- [ ] 第二次失败 Build 仍显示并运行 v1；失败 Candidate 可诊断。
- [ ] Restore v1 产生新 Candidate，不改写 v1。

**日终验收：** C12-C15 Done。

**Stop-the-line：** 17:00 前不能安全 Promote Playable，则 C16-C18 不开始；当晚只修 TestReport/transaction/pointer 问题。

---

### 8 月 18 日（周二）：C16 Release + C17 Resources + C18 Cross-project Reuse

**当日目标：** 完成真实 `Playable → Release → Resource Review → SavedResource → 第二 Project 推荐/使用`。

#### zhao — C16 `release-publishing`（1.5h）

- [ ] 实现 Release draft/review/publish/error/retry API 和 Vue modal/detail。
- [ ] Publish 只接受指定 PlayableVersion，幂等创建 immutable Release。
- [ ] Publish 后创建 release-scoped ResourceCandidate batch；空批次返回 0。

#### zhao — C17 `resource-review-library`（2.5h）

- [ ] 实现 ResourceCandidate/SavedResource repositories、provenance、save/ignore/undo 和 pending preservation。
- [ ] Resource Review 改读真实 batch；保存不自动跳下一项，离开 saving 后仍完成或恢复明确状态。
- [ ] 我的资源改读真实 API，完成 gallery/search/filter/detail/edit name/description。

#### zhao — C18 `cross-project-resource-reuse`（2h）

- [ ] 实现 structured compatibility/match API 和推荐/dismiss/use/cancel workflow repository。
- [ ] use 保存 first-use immutable relationship snapshot，只修改资源拥有字段。
- [ ] cancel 只恢复关系字段；普通 GameSpec revision 和导航不清除 dismiss。
- [ ] 第二个真实 Project 通过 K01/Game Design/GameSpec 触发推荐，不使用 demo seed。

#### zhang — Runtime hardening + Review（6h）

- [ ] 完成 OpenGame create/modify/rebuild-from-playable 的最终选择和 contract verification。
- [ ] 跑 timeout/cancel/path escape/invalid artifact/provider failure integration matrix。
- [ ] Review C16-C18 的 artifact/provenance 边界，确保资源流程不访问 untrusted workspace。
- [ ] 修复真实第二 Project Build 所暴露的 Adapter/runtime 问题。

#### 日终 Gate

- [ ] Project A：真实 Playable v1 → Release v1 → 保存至少一个 gameplay SavedResource。
- [ ] My Resources 从 0 → 1，刷新后仍为 1，编辑名称/说明同步。
- [ ] Project B：真实创建 → GameSpec 推荐 Project A 资源 → use/cancel/dismiss 持久化。
- [ ] 两个 Project 和一个全局 SavedResource library 状态互不污染。

**日终验收：** C16-C18 Done；完整功能链第一次真实贯通。

**功能冻结：** 17:00 后不增加字段、页面、资源类型或产品功能，只允许修复 C19 阻塞问题。

---

### 8 月 19 日（周三）：C19 Clean E2E + Deployment + Failure Matrix + Rehearsal

**当日目标：** 在干净环境重复完整真实链路，冻结展示版本和恢复方案。

#### 09:30–12:00 — 双方完成 C19

- [ ] 从 clean database/clean workspace 启动 FastAPI、Vue、SQLite migrations 和 OpenGame runtime。
- [ ] 跑自动化全套：backend unit/integration、runtime contract、安全 tests、frontend typecheck/build、browser E2E。
- [ ] 浏览器 E2E 完成 Project A 全链、Project B 资源复用、failure/cancel/retry/refresh/restore。
- [ ] 验证 artifact URL、SSE reconnect、current Playable safety 和 provenance。
- [ ] zhang Required Review C19 evidence；zhao 合并并标记 C19 Done。

**12:00 硬冻结：** 禁止新功能、schema migration 重写、UI 重构、依赖升级和 OpenGame 版本变化。

#### 14:00–15:20 — 展示环境准备

- [ ] 建立可恢复的展示数据库 snapshot，其中包含一次真实成功 Project A/Release/Resource 和 Project B。
- [ ] 预热依赖与 OpenGame cache，但现场 Build 仍实际调用 OpenGame。
- [ ] 保存最后一次真实成功 run/artifact，作为 OpenGame 临时波动时的“已完成真实运行记录”恢复入口，不伪装成现场新结果。
- [ ] 写 health-check 命令、服务启动顺序、端口、日志路径和一键恢复步骤。

#### 15:20–17:00 — 两轮完整彩排

- [ ] 第一轮按正常现场脚本，全程计时并记录每一段耗时。
- [ ] 第二轮注入一次 Build failure，证明旧 Playable 保持，再 retry 成功。
- [ ] 两轮均验证中文 UI、Projects 列表、Preview、Release、Resource Review、我的资源和第二 Project 推荐。

#### 日终 Gate

- [ ] 所有测试 green；两轮彩排完成；单轮展示不超过 15 分钟。
- [ ] `main`、展示 commit、OpenGame 版本、数据库 migration 和恢复 snapshot 均冻结并记录。
- [ ] 没有未提交 source、未 Review contract 或依赖本地 fixture 的正常路径。

**加时规则：** 只修复 P0：服务无法启动、真实 Build 无法完成、数据丢失、错误 Playable pointer、展示主路径崩溃。视觉细节和非主路径问题记录但不改。

---

### 8 月 20 日（周四）：展示日

**当日原则：** 不实现功能；不升级依赖；不修改 schema；只允许阻塞展示的最小修复。

#### 展示前 90 分钟

- [ ] 从冻结 commit 启动全部服务并运行 health check。
- [ ] 验证 OpenGame 固定版本、credential、磁盘空间、端口和 artifact hosting。
- [ ] 用单独 smoke Project 跑一次短 Build，不污染正式展示 Project。
- [ ] 验证恢复 snapshot 和最近真实成功 artifact 可访问。
- [ ] 关闭自动更新、无关服务和可能占用端口/CPU 的任务。

#### 最终展示脚本（12–15 分钟）

1. Projects 空态/项目列表：说明多 Project 持久化。
2. 输入 Idea，完成 Game Design 和 GameSpec Human Confirm。
3. 发起真实 OpenGame Build，展示 SSE 进度；切走 Workspace 再回来证明任务持续。
4. 展示 BuildCandidate 与 TestReport；手动 Promote 为 PlayableVersion。
5. 发起一次 Change 或 Restore，说明失败不破坏旧 Playable。
6. Publish Release，进入 Resource Review，保存 gameplay resource。
7. 打开“我的资源”，展示来源、详情和编辑同步。
8. 创建/打开 Project B，在 GameSpec 中展示推荐、use、cancel/dismiss。
9. 回到 Projects，展示两个项目独立状态和共享资源库。

#### 现场故障处理顺序

```text
页面问题 → 刷新并从 API 恢复同一状态
SSE 断开 → 重新连接并从 last sequence replay
OpenGame 暂时失败 → 展示失败保护和 retry
外部 CLI 持续不可用 → 打开冻结的真实成功 run/artifact，明确说明这是彩排中实际生成的记录
数据问题 → 停止操作，恢复冻结数据库 snapshot，重新开始该段
```

禁止把 Fake Agent、demo seed 或静态 fixture 冒充现场真实 Build。

---

## 4. Change 完成日期总表

| 日期 | zhao 完成 | zhang 完成 | 当日真实能力 |
|---|---|---|---|
| 8/13 | C00 | C08 | Contract 冻结；真实 CLI 可重复运行 |
| 8/14 | C01, C02 | C09 | FastAPI/SQLite/领域持久化；可靠 Executor |
| 8/15 | C03, C04, C05, C06 | C06 Required Review；C10 parser | Idea → confirmed GameSpec 持久化；Agent contract 冻结 |
| 8/16 | C07, C11 | C10；C13 第一阶段 | 真实 OpenGame Build → BuildCandidate + SSE |
| 8/17 | C12, C14, C15 | C13；C12/C14 Required Review | Candidate → Test PASS → Human Promote → Playable |
| 8/18 | C16, C17, C18 | Runtime hardening；C18 Required Review | Release → Resource → 第二 Project 复用 |
| 8/19 | C19 | C19 Required Review | Clean E2E、部署、失败矩阵、两轮彩排 |
| 8/20 | 展示 Owner | Runtime/故障配合 | 12–15 分钟完整真实展示 |

---

## 5. 每日验证命令基线

C00 会冻结最终命令名称；冻结后每天使用同一组命令，不允许个人替换成更弱验证：

```bash
cd backend
python -m pytest

cd ../frontend
npx vue-tsc -b
npx vite build

cd ..
# 运行 C06 冻结的 GameAgent contract suite
# 运行当天 Change 对应的 integration/browser acceptance
git status --short
```

从 8 月 16 日开始，每日还必须完成一次真实 OpenGame smoke；从 8 月 18 日开始，每日必须完成一次 Project A → Project B 的真实跨项目 smoke。

---

## 6. 进度控制与升级规则

### P0 Blocker

- Contract 无法达成双方一致。
- OpenGame 无法非交互运行或无法稳定找到 artifact。
- Migration/transaction 会损坏或串联 Project 状态。
- Build failure/cancel 会改变 current Playable。
- TestReport 缺少证据仍能 Promote。
- Refresh/返回页面会重复创建 run。
- Release/Resource provenance 指向错误 Project/Version。

P0 出现后，两人停止各自后续 Change，共同处理到恢复日终 Gate。

### P1 Blocker

- 非主路径 API 错误文案、次要 UI、非展示资源类型、性能优化。

P1 不阻塞当日 Gate时进入 8 月 19 日上午修复队列；12:00 后延期到展示后。

### 不允许的“赶进度”方式

- 用 frontend local state 替代未完成 backend persistence。
- 用 FakeGameAgent 替代真实 OpenGame E2E。
- 省略 Candidate/TestReport/Human Promote，直接生成 Playable。
- 把 Playable 发布和 Resource 保存合并为自动动作。
- 为了省时间让 Adapter/Agent 直接写 Project DB。
- 跳过 Required Review 或把未集成 branch 计为完成。

---

## 7. 最终 Definition of Done

- [ ] C00-C19 全部合并到 `main`，对应 OpenSpec 与实现一致。
- [ ] 两个真实 Project 存在于 SQLite，刷新/重启后恢复。
- [ ] OpenGame 真实生成浏览器 artifact，Executor/Adapter 边界可替换。
- [ ] RunEvent/SSE 可重连，刷新不重复启动 Build。
- [ ] BuildCandidate 与 current Playable 分离，failure/cancel 不破坏 Playable。
- [ ] TestReport evidence 由平台校验，Human Promote 创建不可变 PlayableVersion。
- [ ] Human Publish 创建不可变 Release 和 release-scoped ResourceCandidate batch。
- [ ] Resource Review/My Resources 持久化，编辑同步且 provenance 正确。
- [ ] Project B 真实获得并使用 Project A SavedResource；cancel/dismiss 正确。
- [ ] Clean-environment tests 和两轮完整彩排通过。
- [ ] 8 月 20 日展示使用冻结 commit、固定 OpenGame 版本和已验证恢复方案。
