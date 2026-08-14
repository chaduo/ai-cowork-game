# AI Cowork Game V1 — Design Spec

**Date:** 2026-08-14
**Status:** Approved / Frozen
**Scope:** AI Cowork Game V1
**Game Runtime:** Phaser 2D / Browser
**Primary Mode:** Single-user AI game-development workspace

---

# 1. Product Definition

AI Cowork Game 是一个 **AI 游戏开发工作台**。

它面向：

* 没有完整开发能力、希望通过自然语言制作游戏的普通用户；
* 希望使用 AI 提高设计、开发和迭代效率的独立开发者。

产品核心不是：

`Prompt → Generate Game → End`

而是持续的人机协作生命周期：

`Idea → Design → GDD → GameSpec → Build → Verify → Play → Modify → Release → Reuse`

V1 仅支持：

**Phaser 2D 浏览器游戏。**

---

# 2. Core Product Principle

AI Cowork Game 应被设计为：

> **一个确定性的产品状态机，包裹一个非确定性的 Agent Runtime。**

AI Cowork Game 负责：

* 项目状态
* Human Gate
* GDD / GameSpec
* Change
* BuildJob
* Candidate / Playable
* Verification
* Version
* Git Mapping
* Release
* Resource provenance

Agent 负责：

* 理解
* 推理
* 规划
* 生成
* 修改
* Debug
* Repair
* Adapt

Agent 可以提出：

`READY / PROPOSE / RECOMMEND / NEEDS_INPUT`

但不能自行完成关键产品状态转换。

---

# 3. V1 Lifecycle

完整生命周期：

```text
Projects
   ↓
Create
Idea / Prompt Template
   ↓
Game Design
Brainstorming
   ↓
GDD
   ↓
Design Readiness
   ↓
Human Confirm
   ↓
GameSpec
   ↓
Human Review
   ↓
Human Confirm
   ↓
Build
   ↓
Candidate
   ↓
Automated Verification
   ↓
Human Play Review
   ↓
Promote
   ↓
Playable
   ↓
Modify / Iterate
   ↓
New Candidate
   ↓
New Playable
   ↓
Publish
   ↓
Release
   ↓
Resource Extraction
   ↓
My Resources
   ↓
Future Project Reuse
```

用户 UI 不展示全部内部阶段。

顶部生命周期保持：

`DESIGN → GAMESPEC → BUILD → PLAYABLE`

---

# 4. Project Home

Projects 首页采用状态驱动项目卡。

每个项目至少展示：

* 当前阶段
* 最新 Playable
* Build 状态
* 最新 Release
* 下一步动作

进入已有项目时，根据项目当前状态决定落点：

```text
Build running
→ Build Progress

Verification failed
→ Verification Result

GameSpec awaiting review
→ GameSpec Review

GDD awaiting confirmation
→ Game Design

正常开发
→ 上次 Workspace

无待处理事项且已有 Playable
→ Preview / Playable
```

V1 为单用户模式。

不做多人协作、权限和实时共同编辑。

---

# 5. Project Navigation

项目内部保留两层导航。

## Lifecycle

```text
DESIGN
GAMESPEC
BUILD
PLAYABLE
```

用于表达：

> 项目生命周期目前到了哪里。

## Workspace

Build 后主要包含：

```text
修改
PREVIEW
ASSETS
CODE
```

其中：

* Preview 是 Build 后的主要 Workspace；
* 修改是 AI Cowork 的持续迭代入口；
* Assets 和 Code 是专业能力；
* 专业能力不得抢占 Playable 的中心位置。

未生成内容与正在构建必须区分：

```text
not_ready ≠ building
```

可以存在：

`等待构建 / 正在构建 / 验证中 / 可用 / 构建失败`

等内部状态。

---

# 6. Create

项目支持两种起点：

## Natural Language Idea

用户直接输入：

> 做一个经营咖啡店，同时可以和 NPC 培养关系的游戏。

## Prompt Template

V1 Template 只提供预设 Prompt。

例如：

* 农场经营
* 平台跳跃
* RPG
* 塔防

Template 不携带代码骨架、玩法系统或预制资产。

两种入口最终都进入同一个 Game Design 流程。

---

# 7. Game Design Brainstorming

Game Design 不是固定问卷。

AI 根据当前设计状态动态判断：

> 当前最重要、最阻塞设计落地的问题是什么？

每轮原则：

1. 读取当前 Game Design State。
2. 判断 Blocking Design Gaps。
3. 如果存在多个缺口，只选择最重要的一个。
4. 优先提供 Choice Cards，同时允许自由输入。
5. 根据回答更新 GDD Draft。
6. 再次评估 Design Readiness。

目标不是完成“100% 完整设计”。

目标是：

> **Minimum Buildable Game Design。**

即足够支持 First Playable 的设计。

---

# 8. GDD Presentation

Brainstorming 以对话为主。

不实时展示一份持续跳动的完整 GDD。

采用阶段性 Summary：

```text
Brainstorming
↓
连续澄清若干关键问题
↓
GDD Summary
↓
继续讨论
↓
Design Ready
↓
Final GDD Review
```

Final GDD Review：

* 默认通过 AI 自然语言调整；
* 专业用户可以直接编辑；
* Confirm 后产生不可变 GDD Version。

---

# 9. Design Readiness

Design Readiness 对用户轻量可见。

例如：

```text
核心玩法       ✓
玩家目标       ✓
成长方向       ✓
角色与世界     ●
第一版范围     ○
```

它用于解释：

> 为什么 AI 还在继续追问。

它不是要求用户逐项填写的 Checklist。

Design Readiness 判断由：

`LLM Semantic Judgment + Deterministic Rules`

共同完成。

AI 可以判断 Ready。

但：

> **Confirm GDD 必须由用户完成。**

---

# 10. GDD Version Model

采用：

`Mutable Draft + Immutable Confirmed Version`

```text
GDD Draft
↓
Human Confirm
↓
GDD v1
```

后续修改：

```text
GDD v1
↓
Revision Draft
↓
Brainstorming
↓
Confirm
↓
GDD v2
```

历史 Confirmed GDD 永远不可修改。

---

# 11. GameSpec

GameSpec 是：

> **人与 Build Agent 之间的执行合同。**

默认是 Human-readable GameSpec，而不是直接向用户展示 JSON / YAML。

V1 核心 Section：

```text
FIRST PLAYABLE TARGET
这一版要验证什么

CORE GAMEPLAY
玩家真正会做什么

WORLD & CHARACTERS
世界、角色、关系

RULES & PROGRESSION
目标、规则、成长

FIRST PLAYABLE SCOPE
这一版先做什么

DEFINITION OF PLAYABLE
做到什么才算完成
```

核心语义：

```text
WHY
First Playable Target

WHAT
First Playable Scope

DONE
Definition of Playable
```

---

# 12. GameSpec Information Depth

GameSpec 默认采用 Review-first，而不是 Edit-first。

普通用户主要：

`Read → AI Adjust → Confirm`

专业用户可以查看：

* Technical Details
* Structured Spec
* Implementation Defaults

底层可以存在：

`Human-readable → Structured GameSpec → Agent Execution Contract`

三层表达。

但三者必须来自同一个 Spec 状态，而不是三个独立事实源。

---

# 13. Design Decision vs Implementation Default

生成 GameSpec 时必须区分：

## Design Decision

决定：

> 游戏是什么。

例如：

* 是否有战斗；
* 关系系统是不是核心玩法；
* 是否存在第二个场景。

必须 Human Decision。

## Implementation Default

决定：

> 具体怎么实现。

例如：

* movement_speed = 180
* relationship_gain = 5
* collision_margin = 4

AI 可以自动补齐。

Implementation Default 应明确标记来源，但默认不需要普通用户处理。

---

# 14. Resource Recommendation in GameSpec

GameSpec 可以检测当前设计需要的 Capability。

例如：

`NPC Relationship`

系统从 My Resources 中发现历史资源后，可以展示：

* 推荐什么资源
* 为什么推荐
* 来源
* Reuse / Extend 方式
* 会影响 GameSpec 哪部分

用户确认后：

```text
GameSpec Draft
→ resource_reference
```

V1 到这里形成设计层 Resource Binding。

---

# 15. Build

只有 Confirmed GameSpec 才允许正式 Build。

点击：

**确认规格并开始构建**

之后自动进入 Build Progress：

```text
正在构建你的游戏…

✓ 准备项目
✓ 实现核心玩法
● 创建角色与场景
○ 验证游戏
```

默认不展示完整 Agent Trace。

底层 Logs 可以保存，但不是核心 UI。

---

# 16. BuildJob

BuildJob 表示一次 Agent 构建过程。

核心状态：

```text
queued
preparing
building
waiting_for_input
verifying
auto_fixing
succeeded
failed
cancelled
timed_out
```

V1 约束：

> 同一个 Project 同一时间最多一个 Active Build。

---

# 17. Build Cancellation

Build 必须可以取消。

```text
running
→ cancelling
→ cancelled
```

取消意味着：

* 当前 Stable Playable 不受影响；
* 本次 Candidate 不允许 Promote；
* 不进入正常 Workspace；
* 不要求用户查看半成品代码；
* 保留必要 Build Record；
* 默认返回 GameSpec Draft。

V1 不做 Pause / Resume Checkpoint。

---

# 18. Build Blocking Conflict

Build Agent 可以自主调整 Implementation Default。

但不能改变设计语义。

如果发现必须进行新的设计选择：

```text
building
↓
NEEDS_INPUT
↓
BuildJob = waiting_for_input
```

例如：

> GameSpec 要求 Emily 下午去花店，但 First Playable 当前没有花店 Scene。

系统向用户提出轻量 Human Gate。

用户决策后继续 Build。

V1 不要求 Runtime 原地恢复。

可以：

```text
保存 Candidate Workspace
+
保存 Build Context
+
记录用户 Decision
+
启动新的 continuation
```

实现相同产品语义。

---

# 19. GameSpec Amendment

Build 中产生的设计性决策不得修改旧 Confirmed GameSpec。

产生：

`GameSpec Amendment Draft`

本次 Candidate 可以使用 Amendment 继续 Build。

但 Promote 前必须：

```text
Human Confirm Amendment
↓
GameSpec vN+1
```

如果用户不确认 Design Amendment，该 Candidate 不允许 Promote。

---

# 20. Candidate Workspace

每次 Build 必须在隔离 Candidate Workspace 中执行。

例如：

```text
Current Playable
Git commit A
     ↓
Candidate Workspace
     ↓
Agent 修改
```

Agent 不允许直接修改 Stable Playable。

因此：

* Build Failed
* Cancel
* Agent 错误
* Verification Failed

都不会破坏当前稳定版本。

---

# 21. Verification

Candidate 不能因为 Agent 声称“完成”就变成 Playable。

必须进入独立 Verification。

V1 Verification：

```text
Build Check
+
Browser Smoke
+
Core Gameplay Acceptance
```

建议使用真实 Browser Runtime。

核心 Gameplay Acceptance 至少验证一条 First Playable Core Path。

例如咖啡店：

```text
启动
↓
玩家移动
↓
接受订单
↓
制作咖啡
↓
完成订单
↓
金币增加
↓
NPC 互动
↓
关系发生变化
↓
结束当天
```

---

# 22. Game Test Hook

Phaser V1 游戏应提供标准 Test Hook。

概念上类似：

```text
window.__GAME_TEST__
```

允许 Verification Harness：

* 读取游戏状态
* 触发测试动作
* 检查订单
* 检查金币
* 检查 NPC 状态
* 检查完成条件

避免仅依赖 Screenshot 猜测游戏是否正确。

---

# 23. Acceptance Severity

Acceptance Criteria 在 GameSpec 阶段就进行分类。

基本规则：

```text
Core Path
→ Critical

Supporting Experience
→ Partial
```

但最终分类必须结合：

* First Playable Target
* Core Loop
* Definition of Playable

例如关系事件如果是本次 First Playable 的核心验证目标，就应该属于 Critical。

Verification 不临时让 LLM 判断严重程度。

---

# 24. Verification Result

三种主要结果：

```text
PASSED
PARTIAL_FAILURE
CRITICAL_FAILURE
```

处理规则：

```text
PASSED
→ 可以试玩
→ 可以进入 Promote Gate

PARTIAL_FAILURE
→ 可以试玩
→ 不允许 Promote

CRITICAL_FAILURE
→ 不进入正常试玩
→ 进入 Auto Fix
```

---

# 25. Automatic Repair

Verification Fail 后：

```text
Test
↓
Failure Report
↓
Agent Diagnose
↓
Scoped Fix
↓
Rebuild
↓
Test
```

最多自动修复：

**3 rounds**

每轮必须记录：

* failure
* diagnosis
* changed scope
* result

超过 3 次：

* Critical Failure → Human Gate / Build Failed
* Partial Failure → 可以试玩，但不可 Promote

Agent 负责：

> Fix。

Verification Service 负责：

> Judge。

---

# 26. Candidate and Playable

Candidate：

> 一次 Build 的候选结果。

Playable：

> 自动验证通过 + 用户实际试玩确认后的稳定版本。

晋升流程：

```text
Candidate
↓
Verification PASS
↓
Human Play Review
↓
Resolve Design Amendment
↓
Promote
↓
Playable
```

任何 Candidate 永远不能自动覆盖当前 Playable。

---

# 27. Playable Version

Playable 是整个系统的稳定开发基线。

必须：

* immutable
* verified
* human accepted
* git backed
* restorable

一个 Playable 应能够追溯：

```text
Playable v7
├─ GDD v3
├─ GameSpec v5
├─ Change #12
├─ Verification #18
└─ Git commit abc123
```

---

# 28. Post-Build Workspace

Build 后以 Play 为中心：

```text
PREVIEW
↓
发现问题
↓
Ask Cowork AI
↓
Change
```

同时提供：

```text
修改
PREVIEW
ASSETS
CODE
```

专业能力按需深入。

---

# 29. AI Modification

修改页面支持：

* AI 推荐下一步改进方向；
* 用户自由输入。

推荐依据：

`GameSpec + Playable + Verification + Current Features`

用户提交修改后：

```text
Modification Request
↓
Change Analysis
↓
Impact Analysis
↓
Low / Medium / High
↓
必要时 Human Gate
↓
Scoped Build
```

---

# 30. Change Impact

Change 分为：

## Low Impact

例如：

* UI
* 文案
* 小数值
* 局部视觉表现

可以自动继续。

## Medium Impact

例如：

* NPC 行为
* 局部玩法规则
* 单资产变化

展示影响范围后快速继续。

## High Impact

例如：

* Core Loop
* 世界结构
* 核心角色定位
* 主要玩法系统

必须 Human Gate。

必要时产生 GDD / GameSpec Revision。

---

# 31. Change History

V1 只保留 Lightweight Change History。

记录：

* 用户原始意图
* AI Summary
* Impact Level
* Affected Scope
* Source Playable
* Result Playable
* Status
* Time

不做 Jira 式需求管理。

---

# 32. Assets Workspace

V1 Assets 支持：

```text
查看
↓
选择单个 Asset
↓
自然语言修改 / 重新生成 / 上传替换
↓
Asset Draft
↓
Preview
↓
Apply / Discard
```

只有 Apply 后：

```text
Asset Draft
→ Candidate
```

试生成多次 Asset 不产生多个正式版本。

---

# 33. Code Workspace

专业用户允许直接查看和修改代码。

采用：

```text
Playable
↓
Code Working Draft
↓
修改多个文件
↓
Diff
↓
Apply / Discard
```

只有 Apply：

```text
Working Draft
→ Candidate
→ Verification
```

不得直接修改 Stable Playable。

---

# 34. Drift Policy

所有变化统一分类为：

```text
Implementation-only
或
Design-semantic
```

## Implementation Override

例如：

* 动画时间变化
* 移动速度变化
* 等价视觉资产替换
* 内部代码重构

允许进入 Playable。

GameSpec 不一定同步。

## Design-semantic Drift

例如：

* Emily 店员 → 花店老板
* 删除关系系统
* 修改 Core Loop
* 改变完成条件

必须最终形成：

* GDD Revision
* GameSpec Revision
* 或 GameSpec Amendment

Design Drift 未解决时不得 Promote。

---

# 35. Publish Review and Overrides

Implementation Override 可以存在于 Playable。

Publish 前必须显式 Review。

例如：

```text
设计一致性
✓ GDD aligned
✓ GameSpec aligned

Implementation Overrides
⚠ 2
```

用户可以选择：

> 保留为实现差异。

设计级 Drift 不允许进入正式 Release。

---

# 36. Versions

Version UI 不是 Git 客户端。

用户主要看到 Playable Timeline：

```text
Playable v7
Emily 下午改为去花店
✓ Verification Passed
GameSpec v5

Playable v6
加强 NPC 关系反馈
✓ Verification Passed
```

点击历史版本可以：

* Play
* 查看 Change
* 查看 Verification
* 查看 GameSpec
* Restore

Git SHA 默认不需要展示。

---

# 37. Restore

Confirmed 历史版本永远不可变。

Restore 不等于：

`reset current version`

而是：

```text
Playable v5
↓
Restore as new Candidate
↓
Verification
↓
Human Review
↓
Playable v9
```

因此历史不会被重写。

---

# 38. Git Strategy

Git 是版本化内容事实源。

进入 Git 的内容包括：

```text
gdd
gamespec
game code
assets
```

关键 checkpoint：

```text
Brainstorming Draft
→ no commit

Confirm GDD
→ Git checkpoint

Confirm GameSpec
→ Git checkpoint

Promote Playable
→ stable Git commit

Publish
→ Git tag / Release snapshot
```

不为每一句 AI 对话产生 Commit。

---

# 39. Database Responsibility

Database 负责：

* Project State
* Current pointers
* BuildJob
* Candidate
* Verification Result
* Change
* Release metadata
* Resource metadata
* Thread metadata

原则：

```text
Git
= versioned content

Database
= product/runtime state
```

两者不能成为同一内容的两个独立事实源。

---

# 40. Release

Publish 不等于 Promote。

```text
Candidate
→ Playable
→ Publish
→ Release
```

Release 是 immutable snapshot。

包含或引用：

* GDD
* GameSpec
* Code
* Assets
* Verification
* Build Artifact
* Implementation Overrides
* Git snapshot/tag

V1 Release 支持：

```text
Play Release
Copy Share Link
Download Build ZIP
Download Source ZIP
```

Release 不单独设置大型导航页面。

挂在 Version Timeline 中即可。

---

# 41. Resource Extraction

只有 Release 可以产生正式可复用 Resource。

```text
Release
↓
AI Resource Extraction
↓
Resource Candidate
↓
Human Review
↓
Approved Resource
↓
My Resources
```

Agent 负责：

> 发现候选。

人负责：

> 决定是否入库。

---

# 42. My Resources

My Resources 是：

> 用户级全局资源库。

不是 Project 内资源库。

Resource 保留 provenance：

```text
Source Project
Source Release
Source Playable
Verification
```

---

# 43. Resource Model — V1 Lite

产品概念采用：

`Capability + Implementation`

但 V1 不做真正的软件 Package 抽象。

Resource 至少保存：

```text
name
description
capabilities
source_release
verification
implementation_refs
basic_dependencies
```

Implementation 可以只是：

> 一组经过 Review 的历史源文件 / 目录引用。

---

# 44. Resource-assisted Build — P0-lite

Resource Reuse 最小执行闭环提升为 **P0-lite**。

必须做到：

```text
Project A Release
↓
Resource Extraction
↓
Human Review
↓
My Resources

Project B GameSpec
↓
Resource Recommendation
↓
Human Confirm
↓
resource_reference
↓
BuildRequest
↓
Build Agent 获得历史实现上下文
↓
参考 / 复制 / Extend
```

V1 不要求即插即用。

成功标准是：

> 用户选择的历史 Resource 确实进入 Build Agent Context，而不是只停留在 UI。

---

# 45. Resource V1 Non-goals

V1 不做：

* 自动把业务代码泛化成通用组件
* npm package 自动生成
* 完整 dependency graph
* 自动跨项目兼容证明
* 通用组件组合系统
* 零修改即插即用

V1 允许 Agent：

`REFERENCE / COPY / EXTEND / IGNORE`

---

# 46. Conversation Model

Conversation 不作为 Project Fact Source。

采用：

> 项目级统一结构化状态 + UI 按阶段 / Task 分线程。

例如：

```text
Game Design
GameSpec Review
Change #12
Change #13
Asset Edit · Emily
```

---

# 47. Agent Context

不同 Thread 不共享全部聊天历史。

采用：

```text
Agent Context
=
Current Project State
+
Current Task State
+
Relevant Project Data
+
Current Thread History
```

称为：

> **Task-scoped Context Assembly**

例如 Build Agent 只需要：

* Confirmed GameSpec
* Base Playable
* Affected Scope
* Resource References
* Relevant Overrides
* Candidate Workspace

而不是整个项目所有历史对话。

---

# 48. Agent Profiles

V1 不建立复杂 Multi-Agent 系统。

采用：

```text
One Agent Runtime

├─ Game Design Profile
├─ GameSpec Profile
└─ Game Build Profile
```

另外：

* Change Analysis
* Resource Extraction

可以作为一次性 Structured Inference。

Verification 不是 Agent。

---

# 49. Game Design Profile

负责：

* Idea understanding
* Gap Analysis
* Dynamic Clarification
* Choice generation
* GDD patch
* Readiness assessment

不能：

* Confirm GDD
* 修改项目 phase
* Build game

---

# 50. GameSpec Profile

负责：

* GDD → GameSpec
* Implementation Defaults
* Acceptance Criteria
* Resource Requirements
* Unresolved Design Decision detection

不能：

* Confirm GameSpec
* 自己决定 Human Design Decision

---

# 51. Game Build Profile

负责：

* Build Planning
* Read/Edit/Run
* Phaser implementation
* Resource adaptation
* Implementation Default adjustment
* Test failure diagnosis
* Scoped repair

不能：

* 修改历史版本
* Promote
* Publish
* Approve Resource
* 擅自改变设计语义

---

# 52. Agent Runtime Boundary

Agent Runtime 是可替换基础设施。

统一抽象目标：

```text
start
events
result
cancel
```

未来可以实现：

```text
ClaudeRuntime
PiRuntime
OpenGameRuntime
OtherRuntime
```

Product Core 不依赖具体 Runtime。

---

# 53. Agent Orchestrator

AI Cowork 自己实现 Agent Orchestrator。

职责：

* Context Assembly
* Profile Selection
* Tool Policy
* Path / Scope Policy
* Runtime Invocation
* Structured Output Validation
* Cancel
* Timeout
* Runtime Event Normalization

它是：

> AI Cowork Game 与通用 Agent Runtime 之间的领域适配层。

---

# 54. Backend Architecture

推荐：

```text
Frontend
Vue
    ↓ HTTP / SSE

FastAPI
Application Core
    │
    ├─ Project Service
    ├─ Design Service
    ├─ GameSpec Service
    ├─ Change Service
    ├─ Build Service
    ├─ Version Service
    ├─ Release Service
    └─ Resource Service
    │
    ▼
Agent Orchestrator
    ↓
Agent Runtime
    ↓
Candidate Workspace
    │
    ├─ Git
    └─ Verification Service
```

Frontend 不直接控制 Agent。

---

# 55. Build Events

Runtime 内部事件需要被 Orchestrator 转换成平台统一事件。

例如：

```text
build.started
build.phase_changed
build.needs_input
verification.started
verification.failed
build.auto_fix_started
build.completed
build.failed
```

通过 SSE 提供给 Frontend。

前端不需要理解某个具体 Agent Runtime 的 Tool Trace。

---

# 56. Human Gates

V1 核心 Human Gate 控制在六类：

1. **Confirm GDD**
2. **Confirm GameSpec**
3. **Blocking Build Decision**
4. **Promote Candidate**
5. **Publish Review**
6. **Resource Review**

不要把每个 Agent Plan、代码修改或 Auto Fix 都做成审批。

原则：

> AI 尽可能自主工作，只在真正改变产品语义或稳定事实时要求人类确认。

---

# 57. P0

V1 必须形成：

## Design Loop

`Idea → Brainstorming → GDD → GameSpec`

## Build Loop

`GameSpec → Build → Candidate → Verification → Playable`

## Iteration Loop

`Playable → Change → Impact → Rebuild → New Playable`

## Release Loop

`Playable → Release → Share`

## Resource Loop — Lite

`Release → Resource → Future GameSpec → Build Agent Context`

---

# 58. P1

优先增强：

* AI recommended next improvements
* Build waiting_for_input
* GameSpec Amendment
* Lightweight Drift Detection
* Lightweight Change History
* Restore old Playable
* richer technical detail view
* richer Resource matching

如果 Runtime Resume 复杂，`waiting_for_input` 可以通过 Candidate Workspace continuation 实现，而不要求真正暂停 Agent Session。

---

# 59. V1 Explicit Non-goals

V1 不做：

```text
Unity / Godot / 3D
Multi-engine
Native game

Multi-user collaboration
Realtime collaborative editing
Role / Permission system

Parallel Candidates
Git branch UI
Merge UI

Agent Swarm
Planner/Coder/Reviewer multi-agent architecture
Unlimited autonomous repair

Full AI playtesting
AI judgment of “fun”
Full visual QA

Automatic reusable package extraction
Complete dependency graph
Automatic compatibility proof

Steam / itch.io / App Store publishing

Full DAM
Complex asset version trees

Jira-style Change Management
```

---

# 60. V1 Success Definition

AI Cowork Game V1 完成时，应该能够证明：

> 用户可以从一个模糊游戏 Idea 或 Prompt Template 出发，在 AI 的动态设计协作下形成经过确认的 GDD 和 GameSpec；系统根据 GameSpec 在隔离环境中构建 Phaser 2D 游戏，并利用自动 Browser + Core Gameplay Acceptance 验证 Candidate；用户试玩后能够通过自然语言、资产或代码继续修改，产生新的稳定 Playable；Playable 可以发布为可分享 Release；发布版本中经过 Human Review 的能力可以进入 My Resources，并在未来项目中作为 Build Agent 的历史实现上下文被真正复用。

---

# 61. Architectural Invariants

以下原则在 V1 中不得被破坏：

```text
1. Phaser 2D only.

2. Single user.

3. One project → at most one Active Build.

4. Confirmed GDD / GameSpec are immutable.

5. Candidate never overwrites Playable.

6. Playable requires automated verification + human acceptance.

7. Design-level Drift must be resolved before Promote.

8. Implementation Override may remain, but must be reviewed before Publish.

9. Release is immutable.

10. Git stores versioned project content.

11. Database stores product/runtime state and pointers.

12. Conversation is not a fact source.

13. Verification judges; Agent repairs.

14. Agent cannot cross Human Gates.

15. Resource must originate from a verified Release and Human Review.

16. Selected Resource must actually enter Build Agent context.

17. Agent Runtime must remain replaceable.
```

---

# 62. Final Architecture Summary

整个 V1 可以压缩为：

```text
                   AI COWORK GAME

                Product State Machine
                         │
        ┌────────────────┼────────────────┐
        │                │                │
       GDD            GameSpec          Change
        │                │                │
        └──────────────┬─┴────────────────┘
                       ↓
               Agent Orchestrator
                       ↓
                Agent Runtime
                       ↓
             Candidate Workspace
                       ↓
                  Verification
                       ↓
                    Candidate
                       ↓
                 Human Promote
                       ↓
                    Playable
                       ↓
                     Release
                       ↓
                    Resource
                       ↓
                Future Game Build
```

核心产品思想：

> **Design with AI. Build with AI. Verify deterministically. Decide with humans. Evolve through versions. Reuse verified work.**
