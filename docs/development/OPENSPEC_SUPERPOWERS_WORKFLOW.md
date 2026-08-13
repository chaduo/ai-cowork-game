# OpenSpec + Superpowers Development Workflow

> 目标：规定 AI Cowork Game 如何从一个 Change 进入 Spec、Implementation Plan、代码实现、验证与合并。

---

# 1. 两个工具的职责必须分开

## OpenSpec

负责：

```text
What
Why
Scope
Requirements
Acceptance Criteria
Design Boundary
```

它是 Change 的需求事实源。

典型产物：

```text
openspec/changes/<change-name>/
├── proposal.md
├── design.md
├── tasks.md
└── specs/
```

## Superpowers

负责：

```text
Implementation Plan
TDD
Task Execution
Code Review
Verification
```

即：

```text
How
```

## 推荐链路

```text
Change Catalog
↓
Change Brief
↓
OpenSpec
↓
Human Review Gate
↓
Superpowers
↓
Implementation
↓
Verification
↓
PR
```

---

# 2. 不推荐的做法

不要同时：

```text
/opsx:apply
+
Superpowers executing-plans
```

让两个系统同时负责代码实现。

否则可能出现：

- 两套任务拆分
- 重复实现
- Scope 漂移
- 一个 Agent 改完后另一个 Agent 又重新设计
- Spec 与实际实现来源不清晰

本项目约定：

> OpenSpec 负责需求与设计事实源；Superpowers 负责详细实施计划和实现纪律。

---

# 3. Step 0 — 从 Change Catalog 选择 Change

开发前查看：

```text
docs/development/V1_CHANGE_CATALOG.md
```

例如：

```text
C07 build-job-orchestration
```

检查：

```text
Owner
Reviewer
Dependencies
```

如果依赖未满足：

```text
Status = Blocked
```

不要提前实现。

选定 Change 后，先建立隔离 worktree，再开始 Brief、Explore 或 Propose：

```bash
cd /Users/zhaozhuo/workspace/explore/ai-cowork-game
git switch main
git pull --ff-only
git fetch origin
git worktree add .worktrees/<change-name> -b feature/<change-name> origin/main
cd .worktrees/<change-name>
git submodule update --init --recursive
```

从这一步开始，该 Change 的 OpenSpec artifacts、代码、测试和 commit 都只能在这个 worktree 中完成。主目录保持干净，便于同时创建另一个 Change 的 worktree。

---

# 4. Step 1 — 创建 Change Brief

创建：

```text
docs/change-briefs/<change-name>.md
```

模板：

```text
docs/development/CHANGE_BRIEF_TEMPLATE.md
```

例如：

```text
docs/change-briefs/build-job-orchestration.md
```

Change Brief 重点写：

```text
Goal
Background
In Scope
Out of Scope
Inputs
Outputs
Contracts
Acceptance Criteria
Error Cases
Testing
Done
```

Change Brief 不应该写几十步具体实现代码。

---

# 5. Step 2 — 需求探索

如果需求还有明显不确定：

在 Agent Chat 中使用：

```text
/opsx:explore
```

重点解决：

- Scope 是否过大
- Change 是否需要再拆
- Contract 是否明确
- 数据流是否明确
- Acceptance 是否可测试
- 是否存在架构歧义

只有这些问题基本清晰后才进入 propose。

---

# 6. Step 3 — `/opsx:propose`

在 Agent Chat 中执行：

```text
/opsx:propose <change-name>
```

并明确要求读取 Change Brief：

```text
Read:

docs/change-briefs/<change-name>.md

Use it as the scope source for this change.

Requirements:
- Do not expand the scope.
- Preserve all Out of Scope constraints.
- Keep all public interfaces explicit.
- Include testable acceptance criteria.
```

例如：

```text
/opsx:propose build-job-orchestration
```

期望得到：

```text
openspec/changes/build-job-orchestration/
├── proposal.md
├── design.md
├── tasks.md
└── specs/
```

---

# 7. Step 4 — Human Review Gate

生成 OpenSpec 后 **不能直接写代码**。

依次 Review：

## `proposal.md`

检查：

- Why 是否准确
- Change Goal 是否准确
- Scope 有没有扩大
- 是否混入其他 Change

## `specs/`

检查：

- Acceptance Criteria 是否完整
- 输入输出是否明确
- 状态变化是否明确
- Error Case 是否明确
- Contract 是否一致

## `design.md`

检查：

- 架构边界是否正确
- 有没有跨层依赖
- 有没有 OpenGame-specific 逻辑泄漏
- 有没有过度设计 V2

## `tasks.md`

检查：

- 是否覆盖全部 Spec
- 是否包含测试
- 是否任务过大
- 是否夹杂 Out of Scope 内容

---

# 8. Step 5 — 交给 Superpowers Review

推荐输入：

```text
@Superpowers

Read:

openspec/changes/<change-name>/proposal.md
openspec/changes/<change-name>/specs/
openspec/changes/<change-name>/design.md
openspec/changes/<change-name>/tasks.md

First review the change for:
- scope creep
- contradictions
- missing acceptance criteria
- missing error cases
- architecture boundary violations
- unnecessary complexity

Do not expand the scope.

Then use the writing-plans skill to produce a detailed implementation plan.

Requirements:
- TDD
- each task independently testable
- explicit files
- explicit interfaces
- explicit verification commands
- frequent commits
```

---

# 9. Step 6 — Superpowers Implementation Plan

Superpowers 的 Implementation Plan 应进一步细化成：

```text
Task
↓
Write failing test
↓
Run and confirm failure
↓
Minimal implementation
↓
Run and confirm pass
↓
Commit
```

示例：

```text
Task 1 BuildRepository
Task 2 BuildService
Task 3 POST /builds
Task 4 GameAgent invocation
Task 5 failure path
Task 6 integration test
```

每个任务应该：

- 有明确文件
- 有明确接口
- 可单独测试
- 可单独 Review
- 不依赖“稍后补完”

---

# 10. Step 7 — Execute

根据开发环境使用：

```text
superpowers:subagent-driven-development
```

或：

```text
superpowers:executing-plans
```

执行中原则：

1. 不重新定义需求。
2. 不擅自扩大 Scope。
3. 发现 Spec 问题时先修改 Spec，再继续。
4. 每个独立任务完成后测试。
5. 保持小 Commit。
6. 始终在当前 Change 对应的 `.worktrees/<change-name>/` 中执行；不要让 AI 写入主目录或另一个 Change 的 worktree。

---

# 11. Step 8 — Spec 变化规则

实现过程中发现需求问题：

```text
发现问题
↓
停止相关实现
↓
更新 OpenSpec Artifact
↓
重新 Review
↓
继续 Implementation
```

尤其以下 Contract 变化必须通知双方：

```text
GameAgent Contract
API Contract
Project Schema
Build Schema
Version Schema
BuildEvent
```

禁止：

```text
代码已经这么写了，所以 Spec 就算了
```

事实源应该保持一致。

---

# 12. Step 9 — Verification

准备宣称完成前执行：

```text
Unit Tests
Integration Tests
Typecheck
Lint
Build
Relevant E2E
```

并使用：

```text
superpowers:verification-before-completion
```

验证三者一致：

```text
OpenSpec
↕
Code
↕
Tests
```

重点检查：

- 每个 AC 是否有实现
- 每个关键 AC 是否有测试
- 是否做了 Out of Scope
- 是否违反 Contract
- 是否存在虚假成功状态

---

# 13. Step 10 — PR

PR 中必须关联：

```text
Change ID
Change Name
OpenSpec Path
Acceptance Criteria
Tests
```

例如：

```text
C07 build-job-orchestration

openspec/changes/build-job-orchestration/
```

---

# 14. Step 11 — Archive

PR Merge 并完成验证后：

```text
/opsx:archive
```

Archive 前确认：

- Spec 已与最终实现一致
- 所有 Required AC 已完成
- Change 没有残留未完成 Task
- PR 已 Merge
- main 可运行

---

# 15. 完整流程

```text
V1_CHANGE_CATALOG
       │
       ↓
Select Change
       │
       ↓
Create isolated worktree
       │
       ↓
Change Brief
       │
       ↓
/opsx:explore   ← 需求不清时
       │
       ↓
/opsx:propose
       │
       ↓
proposal / specs / design / tasks
       │
       ↓
Human Review
       │
       ↓
@Superpowers Review
       │
       ↓
writing-plans
       │
       ↓
Implementation
       │
       ↓
Tests
       │
       ↓
verification-before-completion
       │
       ↓
PR Review
       │
       ↓
main
       │
       ↓
/opsx:archive

       ↓
Remove merged worktree
```

---

# 16. 冻结规则

整个团队固定遵守：

1. 一个 Change 一个 Owner。
2. OpenSpec 是需求事实源。
3. Superpowers 是实施计划与执行纪律。
4. 开发前必须有明确 AC 和 Out of Scope。
5. Contract 改动必须双方 Review。
6. 不在实现阶段偷偷修改产品 Scope。
7. 不让两个 Agent 同时充当“实现总控”。
