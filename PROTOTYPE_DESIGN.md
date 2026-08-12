# AI Cowork Game Product Prototype Design

**阶段**：Product Prototype
**目标产品**：Platform V2
**原型类型**：Desktop-only、中保真、全 Mock、可连续点击演示
**非目标**：技术架构设计、正式业务实现、真实 Agent 或构建系统

## 1. Prototype Goal

本原型用于验证 AI Cowork Game 最终 Platform V2 的用户交互是否完整、可理解并适合结项演示。
它必须让评审者看到用户与 AI 围绕同一个持久游戏项目持续协作，而不是观看一组互不关联的生成结果。

原型需要证明五件事：

1. 用户能从一句创意逐步确认 GDD、GameSpec 和素材，再得到第一个可玩 Version。
2. 用户既能通过自然语言让 AI 增量修改，也能直接编辑结构化配置或源码。
3. Candidate 测试失败时，最近成功 Version 仍可试玩，失败证据清楚且能够请求 AI 修复。
4. Version History 能解释每次变化，并能通过恢复历史 Version 产生新的成功 Version。
5. 成功产物可在人工确认后成为 Template、Reusable Asset 或 verified Development Experience，并在后续项目中被看见和使用。

所有内容均使用确定性 Mock Data。Agent 运行使用短暂延时模拟；任何“PASS”“FAILED”“构建”或
“素材生成”都只是产品交互演示，不表示真实执行。

## 2. Core Demo Journey

### 2.1 主项目旅程：Project Alpha

```text
Create Project
→ Idea
→ Generate GDD
→ Direct Edit / AI Mock Edit / Confirm GDD
→ Generate GameSpec
→ Structured Edit / AI Mock Edit / Advanced JSON / Confirm GameSpec
→ Asset Studio
→ Generate Assets
→ Accept / Reject
→ Regenerate one Asset with natural language
→ Accept final Asset set
→ Generate Game
→ AI Progress
→ V1 PASS and Playable
→ AI Modify
→ V2 PASS and Playable
→ Code / Monaco Edit
→ V3 Candidate
→ Test FAILED
→ V2 remains Playable
→ Open TestReport
→ Ask AI to Fix
→ V4 PASS and Playable
→ Version History
→ Restore V2
→ V5 PASS and Playable
```

### 2.2 可复用知识旅程

从 V5 的成功页面点击 **Promote to Reusable Resources**，在同一个人工确认流程中完成：

1. 将 V5 保存为 `Forest Survival Base` Template。
2. 将已接受的 NPC 素材 `Guide Mira` 保存到 Asset Library。
3. 将 V4 对应的成功 Repair 记录为 `Repair unreachable victory condition` verified Experience。

三项资源必须保留各自真实来源：Template 来源是 V5；Asset 来源是 V5 中已接受的素材；Experience
来源是 V4 的成功 Repair Run 和 PASS TestReport。入口来自 V5，不代表三项资源伪装成同一证据。

随后归档 Project Alpha，创建 Project Beta：

```text
Create Project Beta
→ See and select Forest Survival Base Template
→ Asset Studio shows Guide Mira in Reusable Assets
→ Coding progress shows Relevant Experience
→ Verify all three ResourceUse records in mock activity
```

## 3. Information Architecture

### 3.1 Global Shell

```text
Top Bar
├── Product name
├── Active project switcher（原型只显示当前活动项目）
├── Current playable version
├── Active run indicator
└── Demo reset menu

Primary Navigation
├── Project
├── Design
├── Assets
├── Build & Play
├── Code
├── Versions
└── Resources

Main Workspace
├── Page title and current stage
├── Primary work surface
└── Context panel: AI activity / evidence / version status
```

### 3.2 Product Objects

- **Project**：用户与 AI 共同编辑的持续工作对象。
- **GDD**：可直接编辑、可请求 AI Mock Edit、需人工确认的设计文档。
- **GameSpec**：结构化表单与 Advanced JSON 共同表示的游戏事实来源。
- **Asset Set**：具有生成、拒绝、单项再生成和人工接受状态的素材集合。
- **Run**：带阶段、消息和进度的 Mock Agent 执行。
- **Candidate**：尚未通过测试的变更结果。
- **Version**：通过 TestReport 后发布的可玩结果。
- **TestReport**：解释 Candidate PASS、FAILED 或修复依据的结构化证据。
- **Reusable Resource**：经人工晋升的 Template、Asset 或 Experience。

## 4. Global Interaction Principles

### 4.1 Human Gates Are Explicit

GDD Confirm、GameSpec Confirm、Asset Accept、Version Restore 和 Resource Promotion 都必须由用户
点击明确动作完成。Mock AI 可以建议和修改草稿，但不能替用户确认。

### 4.2 Playable Version and Candidate Are Different

所有 Build、Code、Test 和 Version 页面必须同时清楚展示：

- `Playable: V2`：当前稳定、可随时打开的游戏。
- `Candidate: V3 · Test FAILED`：正在处理但不能替换预览的变更。

失败状态使用明确文案“V2 remains playable”，不能只显示红色错误。

### 4.3 AI Changes Are Reviewable

GDD、GameSpec 和代码的 AI Mock Edit 都先显示变更摘要或 diff，用户选择 Apply 或 Discard。
AI 不能在没有可见反馈的情况下静默覆盖用户内容。

### 4.4 One Primary Action Per Stage

每个页面只突出当前阶段的一个下一步动作，例如 `Confirm GDD`、`Accept Asset Set`、
`Generate Game`、`Ask AI to Fix`。次要动作使用普通按钮或菜单。

### 4.5 Progressive Disclosure

- GameSpec 默认显示结构化表单。
- Advanced JSON 通过独立 tab 打开。
- 原始日志默认折叠，当前阶段和用户可理解的消息优先。
- TestReport 先展示结论与失败检查，再展示证据详情。

### 4.6 Mock Behavior Must Be Visible but Not Distracting

原型顶部保留低调的 `Prototype · Mock runtime` 标记。Agent 模拟期间显示真实的阶段变化，不显示
“正在连接 Claude”或“OpenGame 已执行”等误导信息。

### 4.7 Reuse Requires Deliberate Promotion

成功 Version 不会自动进入资源库。用户必须选择资源类型、查看来源证据并确认。一次成功 Repair
最多形成 verified Experience 或 Skill Candidate；原型不出现自动 Skill 修改动作。

## 5. Page List

| ID | Page | Primary Purpose |
|----|------|-----------------|
| P01 | Project Launcher | 创建、归档项目，选择空白起点或 Reusable Template |
| P02 | Design Studio · Idea & GDD | 输入 Idea，生成、编辑和确认 GDD |
| P03 | Design Studio · GameSpec | 结构化编辑、AI Mock Edit、Advanced JSON 和确认 |
| P04 | Asset Studio | 生成、审阅、拒绝、单素材再生成和接受素材 |
| P05 | Generation Progress | 展示 Mock Agent 阶段、消息、日志和取消状态 |
| P06 | Build & Play Workspace | 试玩稳定 Version，并发起 AI Modify |
| P07 | Code Workspace | 浏览文件、Monaco Mock Edit、保存并创建 Candidate |
| P08 | Candidate & TestReport | 展示 FAILED/PASS、稳定预览保护和 Ask AI to Fix |
| P09 | Version History | 查看来源、比较、恢复 Version |
| P10 | Promote Resources | 从成功 Version 人工晋升三类可复用资源 |
| P11 | Resource Library | 查看 Template、Reusable Asset、Experience 和证据 |

## 6. Page Specifications

### P01. Project Launcher

**User Goal**

创建一个新游戏项目，并决定从固定默认模板还是已批准 Reusable Template 开始。

**Main UI**

- Project name 输入框。
- Idea 输入框；Project Beta 可在选择 Template 后补充修改方向。
- `Start from` 选择：`Default Survival Base` 或 `Reusable Templates`。
- Template 列表显示名称、能力标签、来源 Version、PASS 标记和最近验证时间。
- 已有活动项目时显示摘要与 `Continue Project`；归档动作放在菜单中。

**Actions**

- Create Project。
- Select Template。
- Continue Project。
- Archive Current Project。
- Reset Prototype Demo。

**States**

- Empty state：尚无项目和可复用资源。
- Project Alpha creation：只有默认模板。
- Active project exists：禁止创建第二个活动项目。
- Project Beta creation：出现 `Forest Survival Base`。
- Template selected：显示来源和兼容性摘要。

**State Transition**

```text
no_active_project + create → project_draft → P02
active_project + archive_confirm → project_archived → no_active_project
template_selected + create → project_draft(resourceUse created) → P02
```

**Failure UX**

- 名称或 Idea 为空：就地提示，不离开页面。
- 活动项目未归档：阻止创建并提供 `Go to current project`。
- Template 不兼容：禁用选择并说明仅支持 `phaser-survival-v1`。
- Template 证据失效：显示 `Unavailable`，不能继续。

### P02. Design Studio · Idea & GDD

**User Goal**

把一句创意转化为可审阅的简版 GDD，在确认前通过直接编辑或 AI Mock Edit 完善内容。

**Main UI**

- 左侧阶段轨迹：Idea → GDD → GameSpec → Assets → Game。
- Idea 原文区，只读保留最初输入，并提供修改请求输入。
- GDD 编辑器，固定章节：目标、核心玩法、角色、敌人、道具、NPC、胜负条件、美术风格。
- AI 修改侧栏：自然语言输入、变更摘要、Apply/Discard。
- `Confirmed` 状态条和确认时间。

**Actions**

- Generate GDD。
- Direct Edit。
- Ask AI to Edit。
- Apply / Discard AI Suggestion。
- Confirm GDD。
- Regenerate Draft。

**States**

- `idea_ready`。
- `gdd_generating`。
- `gdd_draft`。
- `gdd_ai_suggestion_ready`。
- `gdd_dirty`。
- `gdd_confirmed`。

**State Transition**

```text
idea_ready → generate → gdd_generating → gdd_draft
gdd_draft → direct_edit → gdd_dirty
gdd_draft/dirty → ask_ai → suggestion_ready → apply/discard
gdd_draft/dirty → confirm → gdd_confirmed → P03
```

**Failure UX**

- Mock 生成失败：保留 Idea，显示 Retry 和 `Use demo draft`。
- GDD 缺少章节：Confirm 禁用，并定位缺失章节。
- AI suggestion 不适用：Discard 后原文完全保留。
- 离开 dirty GDD：显示未确认修改提示。

### P03. Design Studio · GameSpec

**User Goal**

理解并调整结构化游戏规则，在确认前可使用表单、AI Mock Edit 或 Advanced JSON。

**Main UI**

- Tabs：`Structured`、`Advanced JSON`、`Changes`。
- Structured 分组：Player、Enemies、Items、Rules、NPC、Art Direction。
- 数值使用输入框、stepper 或 select；NPC 行为限定 idle/patrol/flee。
- AI 修改输入及 suggestion diff。
- JSON 编辑区使用 Monaco 外观，但此阶段只模拟编辑和诊断。
- 固定 schema validation 摘要。

**Actions**

- Generate GameSpec。
- Edit Structured Fields。
- Ask AI to Edit。
- Open Advanced JSON。
- Apply / Discard Suggestion。
- Validate。
- Confirm GameSpec。

**States**

- `gamespec_generating`。
- `gamespec_draft_valid`。
- `gamespec_dirty_valid`。
- `gamespec_dirty_invalid`。
- `gamespec_ai_suggestion_ready`。
- `gamespec_confirmed`。

**State Transition**

```text
gdd_confirmed → generate → gamespec_draft_valid
valid → structured/json edit → dirty_valid or dirty_invalid
valid → ask_ai → suggestion_ready → apply → validate
dirty_valid → confirm → gamespec_confirmed → P04
```

**Failure UX**

- JSON 无效：显示行列、字段路径和恢复上次有效值。
- 超出模板范围：AI suggestion 标为 unsupported，不能 Apply。
- 失去至少一个 NPC 或胜负条件：Confirm 禁用并显示必要条件。
- Structured 与 JSON 冲突：二者始终读取同一 Mock GameSpec，不维护两份状态。

### P04. Asset Studio

**User Goal**

生成并逐项审阅基础素材，拒绝不满意素材，对单个素材用自然语言再生成，最后明确接受素材集合。

**Main UI**

- 分类 tabs：Player、Enemies、Items、NPC、Background、Reusable Assets。
- 素材 tile：预览、名称、类型、来源、状态、prompt 摘要。
- 选中素材详情面板：大图、风格、provenance、prompt、Accept/Reject。
- 单素材 Regenerate 输入框。
- 顶部完成度：`4 accepted · 1 needs review`。
- Project Beta 的 Reusable Assets tab 显示 `Guide Mira` 及来源 V5。

**Actions**

- Generate Assets。
- Accept Asset。
- Reject Asset。
- Regenerate with Prompt。
- Use Built-in Placeholder。
- Reuse Library Asset。
- Accept Asset Set。

**States**

- `assets_empty`。
- `assets_generating`。
- 单项：`pending_review`, `accepted`, `rejected`, `regenerating`, `reusable_selected`。
- 集合：`asset_review_incomplete`, `asset_set_accepted`。

**State Transition**

```text
gamespec_confirmed → generate → assets_generating → asset_review_incomplete
pending_review → accept → accepted
pending_review → reject → rejected
rejected → regenerate(prompt) → regenerating → pending_review
all_required_accepted → accept_set → asset_set_accepted → P05
```

**Failure UX**

- 单素材生成失败：显示 Retry 和 Placeholder，不阻塞其他素材审阅。
- prompt 为空：Regenerate 禁用。
- 来源或许可缺失：不能 Accept 或 Promote。
- 必需类型未接受：`Accept Asset Set` 禁用并列出缺项。
- 复用素材文件失效：标记 unavailable，不复制到项目。

### P05. Generation Progress

**User Goal**

理解 AI 正在做什么，并确信当前步骤、日志、Candidate 和稳定 Version 都处于明确状态。

**Main UI**

- Run 标题、Mock 标识、run ID、elapsed time。
- 阶段 stepper：Preparing → Coding → Installing → Building → Testing → Publishing。
- AI messages 与 tool/log events 混合时间线，可按类别过滤。
- 右侧 Context：confirmed GameSpec、accepted assets、Relevant Experience。
- Project Beta Coding 阶段显示一条 `Relevant Experience`，带 verified 标记和来源 TestReport。

**Actions**

- View Details。
- Expand Build Log。
- Cancel Mock Run。
- Return to Stable Preview（存在稳定 Version 时）。

**States**

- `run_waiting`, `run_coding`, `run_building`, `run_testing`, `run_publishing`。
- `run_cancelled`, `run_failed`, `run_succeeded`。
- Relevant Experience：`none`, `available`, `used`。

**State Transition**

使用 `setTimeout` 依次推进 Mock stage；第一次生成最终进入 V1 PASS，AI Modify 进入 V2 PASS，
代码编辑进入 V3 FAILED，AI Fix 进入 V4 PASS，Restore 进入 V5 PASS。

**Failure UX**

- 失败阶段停留并突出最后成功步骤。
- 若已有 playable Version，始终显示 `Open V2`。
- Cancel 后不伪装成功，也不创建 Version。
- 日志只显示 Mock 内容，不展示密钥或真实宿主路径。

### P06. Build & Play Workspace

**User Goal**

试玩最近成功游戏，并通过自然语言提出下一次增量修改。

**Main UI**

- 大型 iframe-like Mock Game Preview。
- Preview toolbar：Version、Play/Restart、Open full preview。
- 右侧 AI Cowork panel：需求输入、建议范围、Generate Modification。
- 下方当前 GameSpec 摘要、NPC 对话预览和版本来源。
- Candidate 失败时显示不遮挡预览的状态 banner。

**Actions**

- Interact with Mock Game。
- Ask AI to Modify。
- Open Code。
- Open Version History。
- Promote to Reusable Resources（仅成功 Version）。

**States**

- `no_playable_version`。
- `V1_playable`。
- `V2_playable`。
- `V2_playable_with_V3_failed_candidate`。
- `V4_playable`。
- `V5_playable_restored`。

**State Transition**

```text
V1 + AI Modify → P05 → V2 PASS → V2 playable
V2 + Open Code → P07
V3 FAILED → V2 remains playable + P08 available
V4 PASS → V4 playable
V5 PASS → V5 playable + promotion enabled
```

**Failure UX**

- AI 修改输入超出范围：就地给出固定模板限制，不启动 run。
- Candidate FAILED：明确展示失败 Candidate，但 preview version 不切换。
- Preview Mock 异常：提供 Restart，不改变 Version 状态。

### P07. Code Workspace

**User Goal**

直接查看并修改白名单源码或 GameSpec，保存后形成新的 Candidate，而不是直接覆盖可玩 Version。

**Main UI**

- 左侧文件树，区分 editable 与 protected。
- 中间 Monaco-style editor。
- 右侧 Changes、Problems 和 Version baseline。
- 顶部固定显示 `Editing from V2`。
- Demo 文件 `src/game/rules.ts` 中预置一个会导致胜利条件不可达的修改。

**Actions**

- Open File。
- Edit Mock Source。
- Save & Build Candidate。
- Discard Changes。
- View Protected File（只读）。

**States**

- `code_clean`。
- `code_dirty`。
- `local_diagnostics`。
- `saving_candidate`。
- `V3_candidate_created`。

**State Transition**

```text
V2 → edit → code_dirty
code_dirty → save_build → V3 candidate → P05 testing → P08 FAILED
```

**Failure UX**

- 编辑 protected 文件：保持只读并解释白名单边界。
- 本地语法错误：允许继续演示 Save，但明确提示预计构建失败。
- 保存运行中：阻止重复保存。
- 离开 dirty 文件：Discard/Stay 提示。

### P08. Candidate & TestReport

**User Goal**

理解为什么 V3 没有发布，确认 V2 仍安全可玩，并让 AI 根据结构化证据修复。

**Main UI**

- Header：`V3 Candidate · Test FAILED`。
- 稳定保护提示：`V2 remains playable`，附 Open V2。
- TestReport checks：Build PASS、Page Load PASS、Player Movement PASS、NPC PASS、Game Outcome FAIL。
- 失败证据：`Victory threshold cannot be reached within configured game time`。
- 修改文件、来源 `User code edit`、测试时间和 attempt。
- AI Fix panel 自动带入失败摘要，用户可补充要求。

**Actions**

- Open Failed Check。
- Open V2 Preview。
- Ask AI to Fix。
- Return to Code。
- Dismiss Candidate（只改变视图，不删除记录）。

**States**

- `test_running`。
- `test_failed`。
- `repair_requested`。
- `repair_running`。
- `retest_passed`。

**State Transition**

```text
V3 testing → test_failed
test_failed + Ask AI to Fix → repair_requested → P05
P05 repair/retest → V4 PASS → P06
```

**Failure UX**

- TestReport 缺失：显示 `Report unavailable`，禁止发布或修复快捷动作，仅允许 Retry Mock Test。
- Ask AI to Fix 再次失败：保留 V2，增加 attempt，不覆盖原报告。
- 用户关闭页面：顶部全局 Candidate 状态仍可返回。

### P09. Version History

**User Goal**

理解 V1–V5 的来源和关系，比较变化并恢复 V2，同时保留后续历史。

**Main UI**

- 时间线：V1 Initial、V2 AI Modify、V3 Candidate FAILED、V4 AI Repair、V5 Restore from V2。
- Version 行显示状态、来源、摘要、测试、创建时间和 playable 标记。
- Candidate 行使用不同图标和背景，不编号为成功 Version。
- 详情面板：parent、modified files、GameSpec summary、TestReport、preview。
- Restore confirmation 明确“将创建新的 Version，不改写历史”。

**Actions**

- Select Version/Candidate。
- Compare with Parent。
- Open Preview。
- Open TestReport。
- Restore V2。
- Promote Successful Version。

**States**

- `history_ready`。
- `version_selected`。
- `restore_confirming`。
- `restore_running`。
- `V5_published`。

**State Transition**

```text
select V2 → restore_confirming → confirm → P05
P05 build/test PASS → V5(source=restore,parent=V2) → P06/P09
```

**Failure UX**

- 不能 Restore FAILED Candidate。
- Restore Mock 失败：当前 V4 或 V2 stable 指针不变，显示 Retry。
- 来源证据缺失：相关 Promote 动作禁用。

### P10. Promote Resources

**User Goal**

从 V5 的成功上下文中，明确选择并确认要沉淀的 Template、Asset 和 Experience。

**Main UI**

- 三步 wizard，可独立勾选：Template、Accepted Assets、Development Experience。
- 每一步显示 Eligibility、Source、Evidence 和将保存的字段。
- Template：名称、capability、source V5、PASS TestReport。
- Asset：从 V5 accepted assets 中选择 `Guide Mira`，显示 style/prompt/provenance/license。
- Experience：选择 V4 repair run，显示问题、适用条件、行动和 PASS TestReport。
- Final Review 显示三项资源不会自动改变 Formal Skill。

**Actions**

- Select Resource Types。
- Edit Display Name/Applicability。
- Review Evidence。
- Promote Selected Resources。
- Cancel。

**States**

- 单项：`eligible`, `ineligible`, `selected`, `promoting`, `available`。
- wizard：`selecting`, `reviewing`, `promoting`, `complete`, `partial_failure`。

**State Transition**

```text
V5 PASS → open promote → select three → review → confirm
→ template available + asset available + experience available
→ P11
```

**Failure UX**

- 无 PASS TestReport 的 Version：Template ineligible。
- 非 accepted 或许可缺失 Asset：Asset ineligible。
- FAILED repair：Experience ineligible。
- 某一项 Mock promotion 失败：其他成功项保留，失败项可 Retry，不自动回滚为未验证状态。
- 不出现 `Auto-create Skill`；只能在 Experience 详情中看到 `Create Skill Candidate` 次要动作。

### P11. Resource Library

**User Goal**

查看已批准资源、其来源证据和使用记录，并在新项目相应阶段找到它们。

**Main UI**

- Tabs：Templates、Assets、Experiences、Skill Candidates。
- Template 详情：compatibility、source V5、PASS evidence、used by Project Beta。
- Asset 详情：预览、style、type、prompt、provenance、license、source V5。
- Experience 详情：verified 状态、problem、applicability、action、source V4/TestReport、used by Coding run。
- ResourceUse activity：Project Beta seed、asset copy、CodingAgent context。

**Actions**

- Inspect Resource。
- View Source Version/TestReport。
- Create New Project from Template。
- Create Skill Candidate（不自动生效）。
- Retire Mock Resource。

**States**

- `resource_empty`。
- `resources_available`。
- `resource_selected`。
- `skill_candidate_pending_review`。
- `resource_retired`。

**State Transition**

```text
promotion complete → resources_available
template → create project → P01 with template selected
experience → create skill candidate → pending_review only
```

**Failure UX**

- Source evidence unavailable：资源标记 invalid，不能用于新项目。
- Retired resource：历史 ResourceUse 保留，但新 run 不再可选。
- Skill Candidate 创建后明确提示“Not active; review required”。

## 7. Reusable Knowledge UX

### 7.1 Entry Points

- 成功 Version 的 Build & Play 页面：`Promote to Reusable Resources`。
- Version History 的成功 Version 操作菜单：同一入口。
- Asset Studio：accepted Asset 可显示 `Eligible for Library`，但最终 promotion 仍需人工确认。
- 成功 Repair 的 TestReport：显示 `Eligible Experience`，不能自动保存。

### 7.2 Eligibility Language

| Resource | Eligible When | User-facing Evidence |
|----------|---------------|----------------------|
| Template | Version published + PASS TestReport + compatible capability | Source Version、test verdict、schema version |
| Reusable Asset | Asset accepted + provenance/license complete + source Version | Preview、prompt、source、license |
| Development Experience | Development/repair succeeded + Version published + PASS TestReport | Problem、action、applicability、modified files、report |

### 7.3 Discovery in Later Work

- Template 只在 Create Project 的兼容 Template 列表出现。
- Reusable Asset 只在 Asset Studio 的 `Reusable Assets` tab 出现。
- Experience 不要求用户主动搜索；Coding 阶段根据固定 capability/tag 展示一条
  `Relevant Experience`，用户可以展开来源和证据。
- 原型使用确定性精确匹配，不出现搜索质量、相似度或 RAG 文案。

### 7.4 Skill Safety

Experience 详情可以创建 `Skill Candidate`，但必须同时显示：

- `Pending independent review`。
- `Not available to Agents as a Formal Skill`。
- `No automatic modification was made`。

原型不提供批准 Skill、安装 Skill 或编辑正式 Skill 的流程。

## 8. Prototype State Model

### 8.1 Top-level Store

```ts
interface PrototypeState {
  demoStep: DemoStep
  activeProjectId: string | null
  projects: MockProject[]
  design: MockDesignState
  assets: MockAsset[]
  runs: MockRun[]
  candidates: MockCandidate[]
  versions: MockVersion[]
  playableVersionId: string | null
  selectedVersionId: string | null
  resources: MockReusableResource[]
  resourceUses: MockResourceUse[]
  ui: MockUiState
}
```

### 8.2 Main State Regions

| Region | Important States |
|--------|------------------|
| Project | none, draft, active, archived |
| GDD | empty, generating, draft, dirty, suggestion_ready, confirmed |
| GameSpec | empty, generating, valid, invalid, suggestion_ready, confirmed |
| Assets | empty, generating, review_incomplete, accepted |
| Run | idle, waiting, coding, building, testing, repairing, publishing, failed, cancelled, succeeded |
| Candidate | none, pending, testing, failed, passed, published |
| Playable | none, V1, V2, V4, V5 |
| Promotion | idle, selecting, reviewing, promoting, complete, partial_failure |
| Resource | draft, eligible, available, retired, invalid |

### 8.3 Version Invariants

1. `playableVersionId` 只能指向 PASS Version。
2. 创建 V3 Candidate 时 `playableVersionId` 保持 V2。
3. V3 FAILED 后不能创建 V3 Version；历史中显示 Candidate record。
4. V4 PASS 后才将 `playableVersionId` 更新为 V4。
5. Restore V2 创建 V5，`parentVersionId = V2`，不删除 V3/V4。
6. Promotion 不修改 Version、Candidate 或 playable 指针。

### 8.4 Deterministic Demo Events

| Event | Result |
|-------|--------|
| `GENERATE_GDD` | Mock GDD after delay |
| `AI_EDIT_GDD` | One reviewable suggestion |
| `CONFIRM_GDD` | Unlock GameSpec |
| `GENERATE_GAMESPEC` | Valid fixed survival spec |
| `AI_EDIT_GAMESPEC` | Reviewable NPC/rule change |
| `CONFIRM_GAMESPEC` | Unlock Assets |
| `GENERATE_ASSETS` | Five assets; NPC initially rejected in demo |
| `REGENERATE_NPC` | New Guide Mira asset becomes pending review |
| `ACCEPT_ASSET_SET` | Unlock Generate Game |
| `GENERATE_GAME` | V1 PASS |
| `AI_MODIFY_GAME` | V2 PASS |
| `SAVE_CODE_EDIT` | V3 Candidate → Game Outcome FAILED |
| `ASK_AI_FIX` | V4 PASS and verified repair evidence |
| `RESTORE_V2` | V5 PASS |
| `PROMOTE_RESOURCES` | Template + Asset + Experience available |
| `ARCHIVE_ALPHA` | No active project |
| `CREATE_BETA_FROM_TEMPLATE` | Template ResourceUse created |
| `REUSE_ASSET` | Asset ResourceUse created |
| `USE_EXPERIENCE` | Coding context ResourceUse created |

## 9. Page Transition Table

| From | Trigger | Guard | To | Result |
|------|---------|-------|----|--------|
| P01 | Create Project Alpha | No active project | P02 | Project draft + Idea |
| P02 | Confirm GDD | GDD complete | P03 | GDD locked as confirmed baseline |
| P03 | Confirm GameSpec | Spec valid | P04 | GameSpec confirmed |
| P04 | Accept Asset Set | All required assets accepted | P05 | Initial generation run |
| P05 | Initial run PASS | TestReport PASS | P06 | V1 playable |
| P06 | AI Modify | Request in supported scope | P05 | Modification run |
| P05 | Modification PASS | TestReport PASS | P06 | V2 playable |
| P06 | Open Code | V2 exists | P07 | Edit baseline V2 |
| P07 | Save & Build | Dirty editable file | P05 | V3 Candidate |
| P05 | Test FAILED | Game Outcome FAIL | P08 | V2 remains playable |
| P08 | Ask AI to Fix | Valid TestReport | P05 | Repair run |
| P05 | Retest PASS | All checks pass | P06 | V4 playable |
| P06/P09 | Open History | Versions exist | P09 | History selected |
| P09 | Restore V2 | V2 PASS | P05 | Restore Candidate |
| P05 | Restore PASS | All checks pass | P06 | V5 playable |
| P06/P09 | Promote Resources | V5 PASS | P10 | Promotion wizard |
| P10 | Confirm Promotion | Selected resources eligible | P11 | Three resources available |
| P11/P01 | Archive Alpha | No active run | P01 | No active project |
| P01 | Select Template + Create Beta | Compatible Template available | P02/P04 | Project Beta + Template ResourceUse |
| P04 | Reuse Guide Mira | Reusable Asset available | P04 | Asset copied + ResourceUse |
| P05 | Coding stage | Matching Experience available | P05 | Relevant Experience shown + ResourceUse |

## 10. Mock Data Model

### 10.1 Projects and Design

```ts
interface MockProject {
  id: string
  name: string
  idea: string
  status: 'draft' | 'active' | 'archived'
  sourceTemplateId: string | null
  playableVersionId: string | null
}

interface MockDesignState {
  gddMarkdown: string
  gddStatus: 'empty' | 'draft' | 'dirty' | 'confirmed'
  gameSpec: MockGameSpec
  gameSpecJson: string
  gameSpecStatus: 'empty' | 'valid' | 'invalid' | 'confirmed'
  pendingSuggestion: MockSuggestion | null
}
```

### 10.2 Assets

```ts
interface MockAsset {
  id: string
  projectId: string
  kind: 'player' | 'enemy' | 'item' | 'npc' | 'background'
  name: string
  previewUrl: string
  status: 'pending_review' | 'accepted' | 'rejected' | 'regenerating'
  style: string
  prompt: string
  provenance: string
  licenseNote: string
  reusableAssetId: string | null
}
```

### 10.3 Runs, Candidates and Versions

```ts
interface MockRun {
  id: string
  projectId: string
  operation: 'generate' | 'modify' | 'user_build' | 'repair' | 'restore'
  stage: string
  status: 'waiting' | 'running' | 'failed' | 'cancelled' | 'succeeded'
  progress: number
  messages: MockRunEvent[]
  relevantExperienceIds: string[]
}

interface MockCandidate {
  id: string
  label: 'V3 Candidate'
  source: 'user'
  baselineVersionId: 'version-v2'
  status: 'failed'
  testReportId: 'report-v3-failed'
}

interface MockVersion {
  id: string
  number: 1 | 2 | 4 | 5
  source: 'initial' | 'ai' | 'repair' | 'restore'
  parentVersionId: string | null
  status: 'pass'
  testReportId: string
  playable: boolean
}
```

V3 故意不出现在 `MockVersion.number` 中，而是独立 Candidate。界面可以显示“V3 Candidate”，但不能
让用户误以为失败结果是已发布版本。

### 10.4 TestReport

```ts
interface MockTestReport {
  id: string
  candidateId: string
  verdict: 'pass' | 'failed'
  checks: Array<{
    id: string
    status: 'pass' | 'failed'
    evidence: string
  }>
  sourceRunId: string
}
```

### 10.5 Reusable Resources

```ts
interface MockTemplate {
  resourceType: 'template'
  id: 'template-forest-survival'
  name: 'Forest Survival Base'
  sourceVersionId: 'version-v5'
  testReportId: 'report-v5-pass'
  capabilityProfile: 'phaser-survival-v1'
  status: 'available'
}

interface MockReusableAsset {
  resourceType: 'asset'
  id: 'asset-library-guide-mira'
  sourceAssetId: 'asset-npc-guide-mira'
  sourceVersionId: 'version-v5'
  kind: 'npc'
  style: string
  prompt: string
  provenance: string
  licenseNote: string
  status: 'available'
}

interface MockExperience {
  resourceType: 'experience'
  id: 'experience-repair-victory-condition'
  sourceRunId: 'run-repair-v4'
  sourceVersionId: 'version-v4'
  testReportId: 'report-v4-pass'
  problem: 'Victory condition was unreachable before time expired.'
  applicability: string[]
  actionSummary: string
  status: 'available'
}

interface MockResourceUse {
  id: string
  resourceId: string
  targetProjectId: 'project-beta'
  targetRunId: string | null
  usage: 'project_seed' | 'asset_copy' | 'agent_context'
}
```

## 11. Acceptance Checklist

### Core Journey

- [ ] 能从空状态创建 Project Alpha 并输入一句 Idea。
- [ ] GDD 支持 Direct Edit、AI Mock Edit、Apply/Discard 和 Confirm。
- [ ] GameSpec 支持 Structured Edit、AI Mock Edit、Advanced JSON、验证和 Confirm。
- [ ] Asset Studio 能生成五类素材、Reject NPC、自然语言 Regenerate 并接受新素材。
- [ ] Generate Game 显示逐阶段 Mock Progress，并发布 V1 PASS。
- [ ] V1 可试玩，并能通过 AI Modify 得到 V2 PASS。
- [ ] Code Workspace 能模拟 Monaco Edit 并创建 V3 Candidate。
- [ ] V3 Test FAILED 时页面明确显示 V2 remains playable。
- [ ] TestReport 展示 Game Outcome 失败证据。
- [ ] Ask AI to Fix 能产生 V4 PASS，并保留 V3 报告。
- [ ] Version History 同时正确展示成功 Version 和失败 Candidate。
- [ ] Restore V2 创建新的 V5 PASS，不改写 V3/V4 历史。

### Reusable Knowledge

- [ ] V5 成功页提供 Promote to Reusable Resources。
- [ ] V5 能保存为 `Forest Survival Base` Template。
- [ ] accepted `Guide Mira` 能保存到 Asset Library。
- [ ] V4 Repair 能保存为 verified Development Experience，并引用 PASS TestReport。
- [ ] 归档 Project Alpha 后才能创建 Project Beta。
- [ ] Project Beta 创建页能看到并选择现有 Template。
- [ ] Project Beta Asset Studio 能看到并复用 Guide Mira。
- [ ] Project Beta Coding 阶段能显示一条 Relevant Experience。
- [ ] 三类复用分别生成 ResourceUse。
- [ ] Skill Candidate 始终显示 pending review，Formal Skill 不会被自动修改。

### Prototype Quality

- [ ] 所有关键路径只通过点击和输入完成，不依赖刷新、控制台或手工改数据。
- [ ] 所有 Agent 行为均由统一 Mock Store 和确定性延时驱动。
- [ ] 页面刷新策略在原型中有明确选择，不造成状态随机丢失。
- [ ] Desktop 视口下无关键按钮、状态或错误信息重叠。
- [ ] 每个运行页面都显示 Mock runtime 标记。
- [ ] Candidate FAILED 不会改变 playableVersionId。
- [ ] Demo Reset 能恢复到最初 Create Project 状态。

## 12. Open Questions

以下问题不阻塞 Mock Prototype 开始，但需要在 Prototype Review 中确认：

1. **页面组织**：Design Studio 的 GDD 和 GameSpec 应保持两个页面，还是合并为同页 tabs？当前设计采用两个阶段页面，共享同一导航入口。
2. **AI 修改审阅**：GDD/GameSpec 的 AI Mock Edit 是否需要逐字段接受？当前设计采用一次 suggestion 的 Apply/Discard，避免原型过重。
3. **素材接受粒度**：是否允许一次性 Accept All？当前设计要求逐项状态完整，最后统一 Accept Asset Set。
4. **V3 命名**：失败 Candidate 是否应显示为 `Candidate 3` 而不是 `V3 Candidate`，以避免把 Version 编号留洞？当前设计沿用演示脚本的 V3 文案，但视觉上明确标注 Candidate。
5. **Restore 后的 playable 起点**：V5 应完全等于 V2，还是允许包含新的系统元数据？当前设计游戏内容等于 V2，但 Version、来源和 TestReport 是新的。
6. **Promotion 入口**：三类资源是否应在一个 wizard 中晋升？当前设计采用一个入口、三项独立证据和结果。
7. **Experience 可见性**：CodingAgent 使用 Relevant Experience 时，用户是否需要手动批准“Use this experience”？当前设计自动展示并记录 Mock ResourceUse，但不自动改代码。
8. **第二项目深度**：Project Beta 是否必须再次生成到可玩 Version？当前最低原型只验证 Template、Asset 和 Experience 的发现与使用；完整生成可作为评审后扩展。
9. **原型刷新持久化**：使用内存状态还是 localStorage 保留演示进度？建议使用 localStorage，并提供显眼的 Demo Reset。
10. **资源撤销体验**：V2 最低演示是否需要 Retire Resource？当前只在 Resource Library 中保留次要 Mock 动作，不进入主旅程。

## Prototype Scope Guard

本设计确认下一阶段仅实现 Vue 3 + TypeScript + Vite Mock Prototype：统一 Mock Store、Mock Data、
`setTimeout` Agent 模拟、Desktop-only、中保真。不得接入真实 Claude Agent SDK、OpenGame、构建容器、
Embedding、Vector Database、RAG、经验聚类、自动模板抽取或自动 Skill 修改，也不得生成 `tasks.md`。
