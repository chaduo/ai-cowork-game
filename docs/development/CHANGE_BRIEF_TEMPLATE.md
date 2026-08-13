# Change Brief Template

> 用途：一个 Change 准备进入开发时，用本模板明确需求边界。  
> Change Brief 是 OpenSpec 的输入，不是另一个长期维护的正式 Spec。

建议路径：

```text
docs/change-briefs/<change-name>.md
```

例如：

```text
docs/change-briefs/opengame-agent-adapter.md
```

---

# Change: `<change-name>`

## 1. Metadata

**Change ID:** CXX  
**Owner:**  
**Reviewer:**  
**Priority:** P0 / P1 / P2  
**Depends On:**  
**Status:** Backlog / Ready / In Progress / Review / Blocked / Done

---

## 2. Goal

用一句话说明：

> 这个 Change 完成以后，系统获得什么新的、可观察的能力？

示例：

> 通过标准 GameAgent Interface 调用 OpenGame 完成 Phaser 游戏构建，并返回标准 GameBuildResult。

---

## 3. Background

说明为什么需要这个 Change。

重点回答：

- 当前缺什么？
- 为什么现在必须做？
- 它在 V1 闭环中的位置是什么？
- 有没有未来兼容性要求？

示例：

```text
V1 使用 OpenGame 作为底层游戏生成 Agent。
V2 将替换为自研 GameAgent。

因此任何 OpenGame-specific 逻辑必须被限制在 Adapter / Executor 层，
不能泄漏到 BuildService、Project、Workspace。
```

---

## 4. User / System Flow

使用最短链路描述：

```text
Input
↓
Component
↓
Processing
↓
Output
```

示例：

```text
GameBuildRequest
↓
OpenGameAdapter
↓
OpenGameExecutor
↓
OpenGame CLI
↓
GameBuildResult
```

---

## 5. In Scope

明确本 Change 必须实现什么。

- [ ] 
- [ ] 
- [ ] 

要求：

- 必须具体
- 能映射到 Acceptance Criteria
- 不写“完善”“优化”“处理一下”这种模糊描述

---

## 6. Out of Scope

明确本 Change **不允许顺手实现什么**。

- 
- 
- 

这是防止 Scope Creep 的关键部分。

示例：

```text
- 不实现 Workspace UI
- 不修改 Project DB
- 不实现 Version Promotion
- 不改 OpenGame 内核
```

---

## 7. Inputs

列出本 Change 的正式输入。

### Data

```text
...
```

### Interfaces

依赖：

```text
GameAgent Contract
BuildEvent Contract
Project Schema
...
```

### External Dependency

```text
OpenGame CLI
...
```

---

## 8. Outputs

明确产物。

例如：

```text
GameBuildResult
BuildEvent
artifact_path
preview_entry
```

如果是 API：

```text
HTTP status
Response Schema
Error Schema
```

---

## 9. Interfaces / Contracts

列出本 Change 消费和生产的接口。

### Consumes

```text
...
```

### Produces

```text
...
```

### Must Not Depend On

```text
...
```

示例：

```text
OpenGameAdapter must not depend on:
- Vue
- ProjectRepository
- VersionRepository
```

---

## 10. Acceptance Criteria

所有 AC 尽量使用 Given / When / Then。

### AC1 — `<name>`

**Given**

```text
...
```

**When**

```text
...
```

**Then**

```text
...
```

---

### AC2 — `<name>`

**Given**

```text
...
```

**When**

```text
...
```

**Then**

```text
...
```

---

### AC3 — `<name>`

**Given**

```text
...
```

**When**

```text
...
```

**Then**

```text
...
```

---

## 11. Error Cases

必须明确失败路径。

| Scenario | Expected Behavior |
|---|---|
| Invalid input | |
| Dependency failure | |
| Timeout | |
| Partial result | |
| Retry | |

禁止用一句：

```text
Handle errors appropriately.
```

---

## 12. State Changes

如果这个 Change 会修改系统状态，必须明确。

### Before

```text
...
```

### After Success

```text
...
```

### After Failure

```text
...
```

特别检查：

- 是否错误修改 Playable？
- 是否产生脏状态？
- 是否产生重复对象？
- 重试是否幂等？

---

## 13. Testing Requirements

### Unit Tests

- [ ] 
- [ ] 

### Integration Tests

- [ ] 
- [ ] 

### E2E

- [ ] 如本 Change 不需要 E2E，写明“不要求”。

---

## 14. Definition of Done

本 Change 只有同时满足以下条件才能 Done：

- [ ] Goal 已实现
- [ ] 所有 Acceptance Criteria 满足
- [ ] Unit Tests 通过
- [ ] Required Integration Tests 通过
- [ ] Typecheck / Lint / Build 通过
- [ ] 没有实现 Out of Scope 内容
- [ ] 没有违反架构边界
- [ ] Reviewer Approved
- [ ] PR merged to `main`
- [ ] OpenSpec Change 可 Archive

---

# Change Brief Review Checklist

在执行 `/opsx:propose` 前检查：

- [ ] Change 名称使用 kebab-case
- [ ] Goal 能一句话解释
- [ ] 一个 Change 只有一个 Owner
- [ ] Dependency 已明确
- [ ] In Scope 明确
- [ ] Out of Scope 明确
- [ ] Acceptance Criteria 可测试
- [ ] 失败路径已写
- [ ] Interface 已明确
- [ ] 没有提前写大量实现细节
- [ ] 这个 Change 可以独立 Review 和独立 PR
