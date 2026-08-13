# Git Branch & PR Workflow

> 目标：让每一个 Change 都有清晰的 Git 边界、Review 边界和 Merge 边界。

---

# 1. V1 分支模型

两人短周期 V1 推荐：

```text
main
 ↑
feature/*
```

暂不默认引入长期 `develop` 分支。

原因：

- 团队只有两人
- V1 周期短
- 减少额外同步
- 降低长期分支漂移
- PR 直接保护 main 即可

核心要求：

> `main` 永远保持可运行、可演示。

工作目录规则：

```text
主目录（main）
  └── .worktrees/<change-name>/（对应 feature/fix branch）
```

主目录只负责同步和合并；每个 Change 在自己的 Git worktree 中实现、测试和提交。`.worktrees/` 已被 `.gitignore` 忽略，不进入 PR。

---

# 2. Change 与 Branch 的关系

默认：

```text
1 Change
≈
1 Feature Branch
≈
1 PR
```

例如：

```text
Change:
build-job-orchestration

Branch:
feature/build-job-orchestration

PR:
[C07] feat(build): add build job orchestration
```

---

# 3. Branch Naming

统一格式：

```text
feature/<change-name>
```

示例：

```text
feature/project-lifecycle-domain
feature/create-project-flow
feature/game-design-gdd-flow
feature/game-agent-contract
feature/build-job-orchestration
feature/opengame-process-executor
feature/opengame-agent-adapter
feature/opengame-build-event-mapping
feature/workspace-build-preview
feature/version-candidate-playable
```

Change 名称统一：

```text
kebab-case
```

---

# 4. 禁止的分支名

不要按人名：

```text
zhao
zhang
zhao-dev
zhang-dev
```

不要用无语义名字：

```text
feature1
test
new
update
final
final2
fix-all
```

Branch 表达的是：

> 在做什么。

不是：

> 谁在做。

---

# 5. 开始一个 Change

先在主目录同步：

```bash
cd /Users/zhaozhuo/workspace/explore/ai-cowork-game
git switch main
git pull --ff-only
git fetch origin
```

确认 `main` 最新后，创建隔离 worktree 和 branch：

```bash
git worktree add .worktrees/<change-name> -b feature/<change-name> origin/main
cd .worktrees/<change-name>
git submodule update --init --recursive
```

例如：

```bash
git worktree add .worktrees/build-job-orchestration -b feature/build-job-orchestration origin/main
cd .worktrees/build-job-orchestration
```

---

# 6. OpenSpec 与 Branch

推荐顺序（全部在对应 worktree 中执行）：

```text
Select Change
↓
Create worktree + feature branch
↓
Write Change Brief
↓
/opsx:propose
↓
Review
↓
Implementation
```

这样该 Change 产生的：

```text
Change Brief
OpenSpec Artifacts
Code
Tests
```

都在同一个 Feature Branch 中。

---

# 7. Commit 规则

每个 Commit 应该有一个独立意义。

推荐：

```text
feat(build): add build repository
feat(build): add build service
test(build): cover failed agent build
refactor(build): isolate game agent invocation
fix(build): preserve playable on failure
```

不要：

```text
update
done
final
fix
修改
change
test123
```

---

# 8. Commit 粒度

推荐：

```text
test
↓
implementation
↓
test pass
↓
commit
```

而不是开发一天后：

```bash
git add .
git commit -m "done"
```

一个好的 Commit 应该：

- 能解释为什么存在
- 能独立 Review
- 不混入不相关 Change
- 测试状态明确

---

# 9. Push

第一次 Push：

```bash
git push -u origin feature/<change-name>
```

后续：

```bash
git push
```

---

# 10. PR Naming

格式：

```text
[CXX] type(scope): description
```

示例：

```text
[C07] feat(build): add build job orchestration
[C09] feat(agent): add OpenGame adapter
[C11] feat(workspace): show build candidate preview
```

---

# 11. PR Template

```markdown
## Change

CXX `<change-name>`

## Owner

...

## Reviewer

...

## OpenSpec

`openspec/changes/<change-name>/`

## What

本 PR 实现：

- ...
- ...
- ...

## Out of Scope

本 PR 明确不包含：

- ...
- ...
- ...

## Acceptance Criteria

- [x] AC1 ...
- [x] AC2 ...
- [x] AC3 ...

## Tests

执行：

```bash
...
```

结果：

```text
...
```

## Architecture Check

- [ ] 没有违反 Domain Boundary
- [ ] 没有违反 API Contract
- [ ] 没有违反 GameAgent Contract
- [ ] 没有跨 Change 实现无关功能

## Reviewer Focus

请重点 Review：

- ...
- ...
```

---

# 12. Reviewer Checklist

Reviewer 不只是检查“能不能运行”。

必须检查：

## Scope

- 是否满足 Change Goal
- 是否覆盖 AC
- 是否实现了 Out of Scope
- 是否混入其他 Change

## Architecture

- 是否破坏 Contract
- 是否越层调用
- 是否出现重复真相源

对于 OpenGame 相关 Change 特别检查：

```text
BuildService
    ↓
GameAgent
```

不能变成：

```text
BuildService
    ↓
OpenGame CLI
```

对于 Adapter 特别检查：

- 不依赖 Vue
- 不直接修改 Project DB
- 不直接 Promote Playable
- 不泄漏 OpenGame-specific 类型

## Testing

- Unit Tests 是否真实
- Failure Path 是否覆盖
- Integration 是否覆盖必要边界
- 是否存在只测 Happy Path

## Response / State Correctness

- 没有虚假宣称成功
- Build 失败不破坏 Playable
- Candidate / Playable 状态正确

---

# 13. Merge 策略

推荐：

```text
Squash Merge
```

目标：

```text
1 Change
≈
1 main commit
```

Merge 前必须：

- Required Reviewer Approved
- Required Tests Passed
- Verification Completed
- 与最新 main 无冲突
- OpenSpec 与实现一致

---

# 14. 禁止直接 Push main

禁止：

```bash
git push origin main
```

用于功能开发。

标准流程：

```text
feature/<change>
↓
push
↓
PR
↓
review
↓
tests
↓
merge
↓
main
```

---

# 15. Merge 后

先回到主目录同步：

```bash
cd /Users/zhaozhuo/workspace/explore/ai-cowork-game
git switch main
git pull --ff-only
```

清理已合并的 worktree 和本地分支：

```bash
git worktree remove .worktrees/<change-name>
git worktree prune
git branch -d feature/<change-name>
```

如果 worktree 仍有未提交改动，先处理改动再删除；禁止用 `git worktree remove --force` 掩盖未完成工作。

删除远程分支可在 PR Merge 时由 GitHub 自动完成。

然后：

```text
/opsx:archive
```

完成 Change 生命周期。

---

# 16. 并行开发规则

允许：

```text
zhao:
.worktrees/build-job-orchestration

zhang:
.worktrees/opengame-process-executor
```

前提：

- 两个 Change 边界独立
- Contract 已冻结
- 依赖关系允许并行
- 每个 Change 使用不同 worktree，不能共享同一工作目录

如果两人都需要修改同一个核心 Contract：

> 先合并 Contract Change，再开始依赖它的并行 Change。

---

# 17. 冲突处理

发生冲突：

1. 不直接强行选择 ours / theirs。
2. 回看对应 OpenSpec。
3. 判断哪个 Change 拥有该文件或接口的修改权。
4. Contract 冲突必须双方一起 Review。
5. 解决后重新运行测试。

---

# 18. Hotfix

V1 如果 main 出现阻塞 Demo 的问题，可以使用：

```text
fix/<short-description>
```

例如：

```text
fix/build-preview-path
```

Hotfix 也必须 PR。

不要把 Hotfix 当成长期绕过 Change 流程的方式。
