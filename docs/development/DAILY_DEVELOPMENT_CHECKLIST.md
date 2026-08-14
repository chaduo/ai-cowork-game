# AI Cowork Game 每日开发清单

> 用途：zhao 与 zhang 每天从这里开工、验收和收尾。目标不是记录“做过什么”，而是每天把一个可验证的真实纵向切片合并到 `main`。

## 1. 四份文档怎么一起用

每天只按下面顺序看四份文档，不在聊天记录里重新定义范围：

1. [`../product/AI_COWORK_GAME_V1_DESIGN_SPEC.md`](../product/AI_COWORK_GAME_V1_DESIGN_SPEC.md)：确认产品事实、完整 V1 范围和 Human Gate。
2. [`V1_CHANGE_CATALOG.md`](./V1_CHANGE_CATALOG.md)：确认 Change 的目标、Owner、依赖、范围和验收标准。
3. [`V1_FULL_SCOPE_REBASELINE_2026-08-20.md`](./V1_FULL_SCOPE_REBASELINE_2026-08-20.md)：确认今天做哪些 Change、时间盒和日终 Gate。
4. 本文档：执行当天的开工、开发、验证、Review、合并和日终记录。

优先级发生冲突时：

```text
已批准的 V1 Design Spec
> 当前 Change 的 OpenSpec contract
> V1_CHANGE_CATALOG
> 8 月 20 日倒排计划
> 当前实现和聊天记录
```

任何 contract 变化必须先更新 OpenSpec，再更新 Catalog/计划；不能只改代码或只在聊天中达成口头约定。

---

## 2. 每日一页清单

### 09:30 开工（20 分钟）

- [ ] 两人从同一个最新 `main` 开始，工作区无误提交的生成文件或 secret。
- [ ] 主目录只用于同步、查看状态和合并后检查；实现放在 `.worktrees/<change-name>/`。
- [ ] 打开倒排计划中“今天”的章节，写下 zhao、zhang 各自的 Change 和日终 Gate。
- [ ] 对照 Catalog 确认每个 Change 的依赖已经完成。
- [ ] 明确每个 Change 的 Owner、Required Reviewer、branch 和文件所有权。
- [ ] 确认今天是否涉及 contract；如涉及，先冻结 contract 再并行实现。
- [ ] 昨日 blocker 已有处理人和最晚解决时间。
- [ ] 若昨日 Gate 未通过，先追回 Gate，不提前做今天的新功能。

### 09:50 开始实现

- [ ] 一个 Change 一个 branch、一个 Owner、一个 PR。
- [ ] 一个 Change 一个 worktree；worktree 目录名与 branch 的 Change 名一致。
- [ ] 开工前读完 Change Brief 和 OpenSpec artifacts。
- [ ] 先写失败测试或可重复的失败验证，再写最小实现。
- [ ] 业务生命周期修改只通过后端 service/action；Vue 只保留纯 UI 状态。
- [ ] Fake 只用于 contract/unit tests；真实验收使用 SQLite、FastAPI 和 OpenGame。
- [ ] 不顺手实现下一个 Change，不复制状态真相源，不把工作流状态塞入 GameSpec。

### 16:20 集成窗口

- [ ] 停止扩展功能，进入交叉 Review 和纵向验收。
- [ ] zhao Review zhang 的 OpenGame/Executor/Adapter 边界。
- [ ] zhang Review zhao 的 contract、状态机、持久化和 failure path。
- [ ] 运行本日适用的完整验证矩阵并保存 evidence。
- [ ] Required Reviewer 批准后才合并；未通过就修复或明确回滚。

### 17:00 日终 Gate

- [ ] 倒排计划中的当日验收逐条通过。
- [ ] 当天纵向切片已经合并到 `main`，不是只存在于个人 branch。
- [ ] 失败路径不会覆盖当前 Playable、Release 或 SavedResource。
- [ ] 真实命令、API 响应、数据库记录、artifact 或浏览器截图有可追溯 evidence。
- [ ] 更新 Change 状态和日终记录，写明明天第一个动作。
- [ ] 已合并的 Change 已删除对应 worktree；未合并的 worktree 写入日终记录和保留原因。

Gate 未通过时，19:30-21:30 只追回当天 Gate；禁止借加时提前做明日功能。

---

## 3. 今日工作卡

每天 09:30 把下面内容填入当天 PR、协作文档或 `docs/development/daily/YYYY-MM-DD.md`：

```md
# YYYY-MM-DD

今日 Gate：

| Owner | Change | Branch | Reviewer | 文件/Contract 所有权 | 预计合并时间 |
|---|---|---|---|---|---|
| zhao | CXX | feature/cxx-name | zhang | ... | 16:40 |
| zhang | CXX | feature/cxx-name | zhao | ... | 16:40 |

依赖检查：通过 / Blocked（原因）
今日真实纵向验证：
Stop-the-line blocker：无 / ...
```

“今天做后端”“今天接 OpenGame”不算可执行计划。必须写出 Change ID、边界和 Gate。

---

## 4. 开始一个 Change

### 4.1 Ready Gate

- [ ] Change 在 Catalog 和倒排计划中。
- [ ] Goal 只有一个，In Scope / Out of Scope 清楚。
- [ ] 输入、输出、状态变化、错误语义和 AC 可测试。
- [ ] 上游依赖已合并到 `main`，不是只在对方 branch 上。
- [ ] Contract Owner 和 Required Reviewer 明确。
- [ ] 与另一人的文件写入范围没有冲突。

任一项不满足时标记 `Blocked`，不要让 AI 猜 contract 后继续实现。

### 4.2 Branch

```bash
git switch main
git pull --ff-only
git worktree add .worktrees/cxx-change-name -b feature/cxx-change-name origin/main
cd .worktrees/cxx-change-name
```

如果远端没有最新 `origin/main`，先在主目录运行：

```bash
git fetch origin
```

紧急修复使用 `fix/cxx-description`，例如：

```bash
git worktree add .worktrees/fix-build-preview -b fix/build-preview origin/main
```

不直接改 `main`，不在一个 branch 混入多个 Change，也不要在两个 worktree 中同时签出同一个 branch。

worktree 的固定规则：

- 主目录保持在 `main`，只做 `fetch/pull`、查看状态和合并后清理。
- 实现、测试、OpenSpec artifacts 和 commit 都在对应的 `.worktrees/<change-name>/` 中完成。
- 第一次进入新的 worktree，先执行 `git submodule update --init --recursive`；前端依赖按项目要求执行 `npm ci`。
- `.worktrees/` 是本机目录，已经写入 `.gitignore`，不提交其中任何文件。

结束一个已合并 Change：

```bash
cd /Users/zhaozhuo/workspace/explore/ai-cowork-game
git switch main
git pull --ff-only
git worktree remove .worktrees/cxx-change-name
git worktree prune
git branch -d feature/cxx-change-name
```

如果 worktree 仍有未提交文件，不要使用强制删除；先保存、提交或明确丢弃后再清理。

### 4.3 Change Brief 与 OpenSpec

Change Brief 放在：

```text
docs/change-briefs/<change-name>.md
```

模板：[`CHANGE_BRIEF_TEMPLATE.md`](./CHANGE_BRIEF_TEMPLATE.md)

需求仍有歧义时先执行 OpenSpec Explore；边界已经明确时再 Propose。Review 以下 artifacts：

- `proposal.md`：Why、Goal、Scope 是否与 Catalog 一致。
- `specs/`：状态转换、AC、错误路径和 contract 是否完整。
- `design.md`：边界是否正确，有无重复真相源或 OpenGame-specific 泄漏。
- `tasks.md`：是否覆盖测试、集成和真实验收，是否能按依赖顺序执行。

OpenSpec 进入 `Ready` 后才能实现。C00 完成后，OpenSpec 是 contract 的事实源。

---

## 5. 使用 AI 开发

每次交给 AI 的任务至少包含：

```text
Change: CXX <name>
Owner: zhao / zhang
Read: Change Brief + OpenSpec artifacts
Implement: 指定 tasks / 文件边界
Do not: 当前 Change 的 Out of Scope
Contracts: 只读哪些、允许修改哪些
Verification: 必须运行的命令和真实 smoke
```

要求 AI：

- 先检查现有代码与 contract，不根据 prototype 猜后端模型。
- 使用 TDD：失败验证 → 最小实现 → 通过验证 → refactor。
- 发现 spec 矛盾立即停在相关边界，报告矛盾，不自行发明第三种语义。
- 只提交明确列出的文件，不清理其他人的工作区变化。
- 完成前展示最新验证 evidence，不能用“之前通过”替代。

可以并行：互不写同一 contract、schema、migration 或组件状态源的任务。

禁止并行：contract 尚未冻结、一个任务消费另一个未合并输出、双方需要改同一 migration/核心状态机、同一浏览器链路正在被两边同时重写。

---

## 6. 实现循环

每个独立 task 都执行：

```text
定位现状与责任边界
→ 写测试或可重复失败步骤
→ 运行并确认按预期失败
→ 最小实现
→ 运行并确认通过
→ 检查 diff 和 scope
→ 小步 commit
```

开发中持续检查：

- [ ] 代码属于当前 Change。
- [ ] 生命周期 mutation 在唯一 service/store action 后面。
- [ ] 数据刷新或页面重进后仍存在，且 Project 之间隔离。
- [ ] BuildCandidate 与 ResourceCandidate 没有混用 schema/repository。
- [ ] Agent 不能 Promote、Publish 或替 Human Gate 做决定。
- [ ] 失败、timeout、cancel、重试和重复请求有明确行为。
- [ ] OpenGame 输出经过校验，不把任意目录直接当 Playable。
- [ ] 没有 secret、绝对本机路径或未净化 stdout/stderr 进入提交。

---

## 7. 验证矩阵

### 所有前端 Change

```bash
cd frontend
npx vue-tsc -b
npx vite build
```

涉及交互时还必须在浏览器逐项执行对应 AC；不能用 build 通过代替交互验证。

### C01 合并后的所有后端 Change

运行 C01 冻结的 backend test 命令，并至少覆盖：

- unit/service tests
- repository + SQLite integration tests
- migration 从空库执行与重复执行
- API happy path 与 error envelope

### C06 合并后的 Contract 消费方

- [ ] 运行 C06 contract suite。
- [ ] FakeGameAgent 与真实 Adapter 输出满足同一 contract。
- [ ] API DTO、domain model、event payload 没有各自演化出同义字段。

### 8 月 16 日起

每天至少一次真实 OpenGame smoke：

```text
真实 CLI
→ Build/Modify
→ BuildCandidate
→ TestReport
→ Human Promote
→ PlayableVersion
```

记录 command/version、build id、candidate id、artifact path/checksum、结果与时间。

### 8 月 17 日起

每天至少一次完整发布链路：

```text
PlayableVersion
→ Human Publish
→ Release
→ ResourceCandidate batch
→ Resource Review
→ SavedResource
```

### 8 月 18 日起

每天至少一次跨项目链路：

```text
Project A SavedResource
→ Project B 推荐
→ 使用前不可变快照
→ 适配 GameSpec
→ 真实 Modify Build
→ 取消仅恢复 NPC/关系字段
```

上述真实 smoke 任一仍依赖 demo fixture、内存状态或 FakeGameAgent，都必须明确标红，不得记为通过。

---

## 8. Commit、PR 与 Review

### Commit 前

- [ ] 测试和验证刚刚运行且通过。
- [ ] `git diff --check` 通过。
- [ ] `git status --short` 中只 stage 当前 Change 文件。
- [ ] 无 dist、缓存、数据库、credential 和无关格式化。
- [ ] commit message 表达一个完整动作。

示例：

```bash
git add <specific-files>
git commit -m "feat(build): persist build candidates"
```

### PR 必须写明

- Change ID 和 OpenSpec 路径。
- 完成内容与 Out of Scope。
- AC 对应的测试/evidence。
- contract、migration 和兼容性影响。
- Reviewer 最需要检查的 failure path。

### Required Reviewer 检查

- [ ] 实现与 spec 一致，没有扩大范围。
- [ ] Contract 没有被偷偷修改。
- [ ] 状态 owner 唯一，刷新后数据不丢。
- [ ] Happy path、failure path 和幂等/重试符合 AC。
- [ ] 测试能在干净环境复现，不只在作者机器通过。
- [ ] 不会破坏 Reviewer 正在开发的 Change。

仅当 `Approved + Tests Pass + Verification Complete + No Conflict` 才 Squash Merge。

---

## 9. Blocker 与 Stop-the-line

以下情况立即停止相关并行实现：

- Human Gate、生命周期或 provenance 语义出现两种解释。
- migration/schema/API/event contract 不兼容。
- 真实 OpenGame 行为与 C08 evidence 不一致。
- Build 失败覆盖 current Playable，或 Publish/Review 自动发生。
- Project A 的状态或资源污染 Project B。
- secret 泄漏、artifact 路径越界或进程无法取消。

处理顺序：

```text
记录最小复现和 owner
→ 冻结受影响的下游 Change
→ 更新 OpenSpec/contract
→ Required Reviewer 确认
→ 添加回归测试
→ 修复并重新跑纵向链路
```

不阻塞主链的视觉小问题、文案问题和 V2 能力进入 follow-up，不占用当日 Gate。

---

## 10. 冻结期规则

### 8 月 18 日：功能闭环日

- C00-C19 主路径必须全部连通。
- 当天之后只接受阻断完整演示的功能修复。
- 记录完整 rehearsal 的耗时和所有手工步骤。

### 8 月 19 日 12:00：硬冻结

- 禁止新增功能、重构、依赖升级和非必要 schema 变化。
- 只处理 P0/P1：无法启动、数据丢失、主链中断、错误项目/版本、真实 OpenGame 失败。
- 固定 demo seed、OpenGame 版本、命令、环境变量和回退 artifact。
- 至少完成两次从空数据库开始的完整 rehearsal。

### 8 月 20 日：展示日

- 只做健康检查和阻塞性修复。
- 展示前运行 startup、migration、health、真实 OpenGame smoke 和 demo project 检查。
- 不临场合并未 rehearsal 的 PR。

---

## 11. 日终记录模板

```md
## YYYY-MM-DD 日终

### Gate
- 结果：PASS / FAIL
- 今日纵向切片：
- Evidence：命令、测试结果、API/build/release/resource id、截图或 artifact

### zhao
- Change / Branch：
- 已合并 PR / commit：
- 未完成：
- Contract 变化：无 / 链接
- 明日第一动作：

### zhang
- Change / Branch：
- 已合并 PR / commit：
- 未完成：
- Contract 变化：无 / 链接
- 明日第一动作：

### Blocker
- P0/P1：无 / owner + 最晚解决时间
- 下游受影响 Change：
- 是否触发 19:30 加时：是 / 否
```

日终不能只写“基本完成”。没有合并、没有 evidence 或 Gate 未通过时，一律写 `FAIL` 并说明恢复计划。

---

## 12. Change 完成定义

一个 Change 只有同时满足以下条件才是 `Done`：

- [ ] OpenSpec tasks 和 AC 全部完成。
- [ ] 实现与测试已由 Required Reviewer 批准。
- [ ] 适用的 typecheck、build、backend、contract、browser/real smoke 全部通过。
- [ ] failure path、持久化、刷新恢复和 Project 隔离已验证。
- [ ] PR 已合并到 `main`，当日纵向链路在最新 `main` 上复验。
- [ ] evidence 和 Catalog 状态已更新，OpenSpec 可以 archive。

只有代码写完、AI 报告完成、branch 上测试通过或页面看起来正常，都不等于 `Done`。

---

## 13. 每天绝对不要做

1. 不让两个人“共同负责”一个普通 Change。
2. 不直接修改 `main`，不在一个 branch 混多个 Change。
3. 不在 AC 或 contract 不明确时让 AI 自行补全语义。
4. 不把 OpenGame-specific 逻辑写入通用 BuildService。
5. 不让 Vue、Agent 或 timer 绕过后端 Human Gate 推进业务状态。
6. 不让失败 Build 覆盖 Playable，不让 Resource Review 自动跳过用户决定。
7. 不用 Fake、fixture、旧浏览器状态冒充真实端到端 evidence。
8. 不在没有运行最新验证时声称完成。
