# AI Cowork Game Frontend Design Direction v0.1

**状态**：Proposed Freeze · Revised 2026-08-11
**适用范围**：Product Mock Prototype + Platform V2 正式前端
**设计输入**：[PROTOTYPE_DESIGN.md](PROTOTYPE_DESIGN.md)、
[spec.md](specs/001-game-creation-mvp/spec.md)、[plan.md](specs/001-game-creation-mvp/plan.md)
**目标视口**：Desktop-first，设计基准 1440 × 900，最低支持 1280 × 720
**设计方法**：遵循 Anthropic `frontend-design` skill 的原则，先冻结具有领域辨识度的方向、布局、
token 和 signature，再进入 Vue 实现

两名开发者确认本文件后，v0.1 同时成为 Mock Prototype 和正式前端的设计基线。后续可以提高视觉
完成度，但不得改变本文件中的信息层级、状态语义、Human Gate、Candidate/Playable 区分和 Artifact
交互模式，除非经过新的联合设计评审。

## Design Thesis

AI Cowork Game 不是聊天机器人套壳，也不是营销型游戏生成器。它是一张面向个人游戏开发者的
**Verified Workshop（验证工作台）**：创意、设计文档、素材、代码、测试证据和可玩版本在同一张
工作台上逐步成熟，AI 是可观察的协作者，用户始终掌握确认和发布权。

产品最有辨识度的视觉元素是 **Playable / Candidate Dual Track（双轨状态栏）**：

```text
PLAYABLE   V2  PASS · 已验证 ━━━━━━━━━━━━━━━━━━━ 打开试玩
CANDIDATE  V3  FAILED · 测试失败 ━ Game outcome ✕ 查看报告
```

这不是装饰。它持续解释产品最重要的事实：Candidate 可以失败，而 Playable 不会因此被覆盖。

## 1. 视觉方向

### 1.1 Direction Name

**Verified Workshop：冷静的制作台 + 可读的验证证据**

视觉语言来自游戏开发中的实际对象：编辑器面板、构建轨迹、素材检查台、测试清单、版本谱系和
运行信号。界面应像一套经过整理的创作工具，而不是传统企业后台，也不是霓虹电竞界面。

### 1.2 Tone

- **Quietly technical**：信息密度较高，但不压迫；边界、层级和状态清楚。
- **Creative where artifacts matter**：游戏预览和素材可以有表现力，平台框架保持克制。
- **Evidence over celebration**：PASS 以稳定、可信表现为主，不使用烟花或夸张庆祝动画。
- **Human-owned**：Confirm、Accept、Restore、Promote 明确是用户动作，不把 AI 描绘为自主主角。

### 1.3 Visual Signature

只在一个地方使用强识别：**Dual Track Rail**。

- 上轨永远表示最近可玩 Version，使用稳定绿色和实线。
- 下轨表示当前 Candidate；无 Candidate 时显示空轨，有运行时使用蓝色动态段，失败时转为红色断点。
- 项目创建后，双轨以紧凑或完整形态出现在所有项目工作页；Project Launcher 和平台级 Resources
  页面不显示。尚无成功 Version 时，上轨明确显示 `尚无已验证 Version`。
- 轨道能点击跳转到 Preview 或 Candidate/TestReport。
- 不使用渐变、发光、粒子或装饰性时间线替代真实状态。

### 1.4 Typography

| Role | Typeface | Use |
|------|----------|-----|
| Latin display / Version | Archivo, 600 | 英文产品名、Artifact 英文类型、Version/Candidate 标识 |
| Chinese display / UI | Noto Sans SC, 500/700 | 中文页面名称、导航、表单、说明、按钮和长文本 |
| Technical / Data | IBM Plex Mono, 400/500 | Run ID、文件路径、JSON、日志、时间、版本来源 |

三套字体必须以锁定版本 WOFF2 随前端发布，不在运行时请求公共字体 CDN。Archivo 不承担中文
排版；中文统一使用 Noto Sans SC，避免中英文 fallback 指标漂移。字体不是本产品唯一 signature，
辨识度由 Dual Track、Artifact 结构和真实游戏素材共同承担。所有 letter spacing 为 `0`；不使用
全大写长句，只有 `PASS`、`FAILED`、ID 和技术枚举保留大写。

### 1.5 Shape and Surface

- 全局以浅色矿物灰画布和白色工作面为主，不使用深蓝/紫色单一主题。
- 页面 section 不做浮动卡片；使用分栏、细边界和轻微表面色差建立层级。
- 只有重复对象使用卡片：Asset Tile、Template Tile、Resource Item。
- 卡片圆角 `6px`；输入和按钮圆角 `4px`；状态标签圆角 `3px`。
- 不使用 pill 作为普通容器，不使用内嵌卡片套卡片。
- 阴影只用于 Dialog、Popover 和拖浮面板；常规工作区用 border 分隔。

### 1.6 Motion

- 页面切换不做大幅转场。
- Agent active stage 使用 1.4 秒低幅度进度扫描；只作用于当前阶段的一条线。
- AI Suggestion Apply 使用 180ms diff 合拢动画。
- Dual Track 更新使用 220ms 位置/颜色过渡，失败时不抖动。
- 支持 `prefers-reduced-motion`，关闭扫描和位移动画。

## 2. Workspace Layout

### 2.1 Global Grid

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ 52 Top Bar: Product / Project / Active Run / Help / Reset                │
├────────────┬─────────────────────────────────────────────────────────────┤
│            │ 64 Workspace Header + Dual Track Rail                      │
│ 216        ├───────────────────────────────────────┬─────────────────────┤
│ Primary    │                                       │ 344 Context Panel   │
│ Navigation │ Main Artifact Workspace               │ AI / Evidence /     │
│            │                                       │ Selection details   │
│            │                                       │                     │
├────────────┴───────────────────────────────────────┴─────────────────────┤
│ Optional 28 Status Footer: Mock runtime / dirty / validation / run ID   │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Stable Dimensions

- Top Bar：`52px`。
- Primary Navigation：`216px`，可折叠为 `56px`，原型默认展开。
- Workspace Header：最小 `64px`；包含 Artifact identity 与 Dual Track。
- Context Panel：`344px`，允许折叠，不随内容自动改变宽度。
- Main Workspace：剩余空间；固定 Context Panel 展开时内容区不得小于 `760px`。
- Status Footer：`28px`，只在 Design、Assets、Progress、Code 和 Test 页面显示。
- 全局页面 padding：`20px 24px`；工具密集页面可降为 `16px`。

### 2.3 Desktop Width Rules

| Viewport | Navigation | Context Panel | Main Workspace |
|----------|------------|---------------|----------------|
| `≥ 1440px` | 216px expanded | 344px fixed | Remaining width, minimum 800px |
| `1366–1439px` | 216px expanded | 320px fixed | Remaining width, minimum 760px |
| `1280–1365px` | 56px icon rail | Closed by default; 344px overlay when opened | Remaining width, minimum 960px before internal padding |

- `1280px` 是受支持的最小宽度；此时不能同时展开完整导航和固定 Context Panel。
- Overlay Context Panel 覆盖 Main Workspace 右侧，不重排 Monaco、preview 或 asset grid；关闭后焦点返回
  触发按钮。
- 在 `1280–1365px`，Asset Studio 从 4 列切换为 3 列；其他页面不得产生横向页面滚动。
- 小于 `1280px` 显示明确的 desktop requirement，不承诺 Monaco 编辑体验；这不影响公开游戏预览。

### 2.4 Page-specific Layouts

| Page Family | Main Workspace | Context Panel |
|-------------|----------------|---------------|
| Project Launcher | 单列创建表单 + Template row | Template evidence |
| GDD | 文档编辑面 | AI suggestion / outline |
| GameSpec | Structured form / JSON | Validation / AI changes |
| Asset Studio | 4-column asset grid | Selected asset review |
| Progress | Stage rail + event stream | Run summary / Relevant Experience |
| Build & Play | 16:9 preview + compact controls | AI Modify composer |
| Code | File tree 220 + Monaco + Problems | Changes / baseline |
| TestReport | Check list + evidence | Candidate and Playable summary |
| Versions | Version table/timeline | Selected record details |
| Resources | Resource list/grid | Provenance / usage |

### 2.5 Density Rules

- 每屏优先展示工作对象，不设置 landing hero。
- 页面标题不超过 `28px`，面板标题不超过 `18px`。
- 固定格式区必须设置稳定宽高：预览 `16:9`、Asset tile `4:3`、图标按钮 `32 × 32`、状态行 `28px`。
- Context Panel 内容过长时独立滚动，不推动 Main Workspace。
- 主操作固定在 Artifact Action Bar 或页面右上角，不能因日志增长下移。

## 3. Navigation

### 3.1 Primary Navigation

顺序与产品旅程一致，但不是一次性 wizard：

```text
项目
设计
  GDD
  GameSpec
素材
构建与试玩
代码
版本
资源
```

- 使用 Lucide 图标 + 文本；折叠状态只显示图标和 tooltip。
- Design 子项只有在 Project 创建后出现。
- 未解锁阶段显示 lock 图标和 gate 原因，不完全隐藏。
- 当前项目归档后，Design/Assets/Build/Code/Versions 进入只读状态。
- Resources 属于平台级导航，未创建项目时仍可访问。

### 3.2 Top Bar

- 左：AI Cowork Game wordmark，不承担页面导航。
- 中：当前 Project 名称与 `Active/Archived` 状态。
- 右：Active Run、Help、Demo Reset；不重复展示 Playable Version。
- Playable/Candidate 事实统一由 Workspace Header 的 Dual Track 表达；Project Launcher 和平台级
  Resources 没有 Dual Track，也不在 Top Bar 创建替代 badge。
- 有 active run 时导航仍可浏览，但会改变项目的动作统一 disabled，并解释“Run in progress”。

### 3.3 Stage Navigation

GDD、GameSpec、Assets、Generate Game 使用小型 gate sequence：

```text
Idea ✓ ─ GDD ✓ ─ GameSpec ● ─ Assets ○ ─ Game ○
```

- `✓` confirmed，`●` current，`○` locked。
- 序列只用于真实有顺序依赖的阶段，不扩散到普通页面。
- 点击已完成阶段可回看；修改 confirmed Artifact 后显示需要重新确认，不自动推进。

### 3.4 Navigation Vocabulary

界面命令使用用户动作：`Confirm GDD`、`Accept asset`、`Save & build candidate`、`Ask AI to fix`、
`Restore V2`、`Promote resources`。不使用 `Submit`、`Execute Workflow`、`Invoke Agent` 等实现语言。

### 3.5 Language Baseline

- 正式界面以简体中文为主要语言。
- 保留用户需要跨文档识别的稳定英文对象名：`GDD`、`GameSpec`、`Candidate`、`Version`、`Run`、
  `TestReport`、`Template`、`Asset`、`Experience`。
- 命令使用中文主动语态：`确认 GDD`、`接受素材`、`保存并构建 Candidate`、`让 AI 修复`、
  `恢复 V2`、`晋升为可复用资源`。
- `PASS`、`FAILED` 和 `Not published` 可作为紧凑状态词，但旁边必须有中文解释；不允许同一动作在
  不同页面交替使用中英文名称。
- Prototype 文案字典与正式前端共用；所有 toast 必须复用触发动作，例如 `确认 GDD` → `GDD 已确认`。

## 4. Design Tokens

### 4.1 Color Tokens

```css
:root {
  --color-canvas: #F2F5F3;
  --color-surface: #FFFFFF;
  --color-surface-subtle: #E9EFEC;
  --color-surface-inset: #DDE6E1;

  --color-ink: #17211F;
  --color-text: #26332F;
  --color-text-muted: #64716C;
  --color-text-disabled: #8D9994;

  --color-line: #CBD5D0;
  --color-line-strong: #9EADA6;

  --color-accent: #176FA6;
  --color-accent-hover: #125B89;
  --color-accent-soft: #DCECF6;

  --color-approved: #0B6F78;
  --color-approved-soft: #D8ECEE;
  --color-verified: #16765E;
  --color-verified-soft: #DDF0E9;
  --color-playable: var(--color-verified);
  --color-playable-soft: var(--color-verified-soft);
  --color-candidate: #A75E12;
  --color-candidate-soft: #F7E8D5;
  --color-failed: #B83A3A;
  --color-failed-soft: #F7DFDF;
  --color-info: #4265A8;
  --color-info-soft: #E1E8F5;
}
```

使用规则：

- 青色表示用户已经完成 Human Gate：GDD/GameSpec Confirmed、Asset Accepted、Restore/Promote 已确认。
- 绿色只表示系统验证完成：PASS、Playable、证据完整且可复用。
- 橙色只表示 Candidate、待审阅、需要人工决定。
- 红色只表示失败、拒绝或阻断性错误。
- 蓝色表示操作焦点、AI active、链接和一般信息。
- 状态不能只依赖颜色，必须同时包含 icon、标签和文本。

### 4.2 Typography Tokens

```css
--font-display-latin: "Archivo", "Noto Sans SC", sans-serif;
--font-body: "Noto Sans SC", sans-serif;
--font-mono: "IBM Plex Mono", "Noto Sans SC", monospace;

--font-size-page-title: 28px;
--line-height-page-title: 36px;
--font-weight-page-title: 700;

--font-size-artifact-title: 20px;
--line-height-artifact-title: 28px;
--font-weight-artifact-title: 700;

--font-size-section-title: 16px;
--line-height-section-title: 24px;
--font-weight-section-title: 700;

--font-size-body: 14px;
--line-height-body: 21px;
--font-weight-body: 400;
--font-weight-body-strong: 600;

--font-size-small: 12px;
--line-height-small: 18px;
--font-size-mono: 12px;
--line-height-mono: 18px;
```

### 4.3 Spacing and Size Tokens

```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;

--control-sm: 28px;
--control-md: 36px;
--control-lg: 44px;
--icon-button: 32px;
--nav-width: 216px;
--context-width: 344px;

--radius-control: 4px;
--radius-card: 6px;
--radius-dialog: 8px;
```

### 4.4 Focus and Elevation

```css
--focus-ring: 0 0 0 3px rgba(23, 111, 166, 0.24);
--shadow-popover: 0 8px 24px rgba(23, 33, 31, 0.14);
--shadow-dialog: 0 18px 48px rgba(23, 33, 31, 0.20);
```

- 所有交互元素必须具有清楚的 keyboard focus。
- 普通卡片和 section 不使用 shadow。
- disabled 不仅降低 opacity，还保留可读标签与原因 tooltip。
- 正文、状态文字和交互控件按 WCAG 2.2 AA 检查；正常文本对比度至少 `4.5:1`，大文本至少
  `3:1`，焦点和非文本状态边界至少 `3:1`。
- Soft 状态背景不能承载低对比度小字；状态正文使用对应深色 token。

## 5. 基础组件

### 5.1 Primitives

| Component | Variants / Rules |
|-----------|------------------|
| `AppButton` | primary, secondary, danger, quiet；命令使用 icon + text |
| `IconButton` | 32px；Lucide icon；必须有 tooltip/aria-label |
| `TextField` / `TextArea` | label、description、error 占稳定空间 |
| `NumberField` | stepper，不使用自由文本模拟数值控制 |
| `SelectMenu` | 小规模固定选项；不使用一排文字按钮 |
| `SegmentedControl` | Structured / JSON、Events / Logs 等互斥模式 |
| `Tabs` | 同一 Artifact 的不同视图，不承担流程推进 |
| `Checkbox` / `Switch` | 多选与二元设置；Accept 不是 switch |
| `StatusMark` | icon + label；非胶囊式大按钮 |
| `Tooltip` | 解释 icon、锁定和 disabled 原因 |
| `Dialog` | Confirm、Restore、Archive、Promote 等不可忽略决定 |
| `Toast` | 结果反馈；文案与触发动作同名 |
| `SplitPane` | File tree/Monaco/Problems 等可调整工作区；必须提供键盘可操作分隔条 |
| `DataTable` | Version、ResourceUse；固定列宽、空值和行操作规则 |
| `Disclosure` | Test evidence、日志和 provenance 的渐进展开 |
| `EmptyState` | 解释当前缺少什么并提供一个明确下一步，不放装饰插画 |
| `ProgressBar` | 只表示已知进度；未知进度使用 stage rail |
| `Skeleton` | Mock/真实数据加载占位；尺寸与最终内容一致，避免布局跳动 |

### 5.2 Domain Components

| Component | Responsibility |
|-----------|----------------|
| `WorkspaceHeader` | 页面/Artifact identity、gate 状态、主操作 |
| `DualTrackRail` | Playable 与 Candidate 双轨事实 |
| `StageGate` | Idea → GDD → GameSpec → Assets → Game |
| `ArtifactFrame` | Draft/Review/Verified 的统一工作面 |
| `ArtifactMetaBar` | 来源、更新时间、schema/version、dirty 状态 |
| `AiSuggestionPanel` | 用户要求、摘要、diff、Apply/Discard |
| `AgentStageRail` | 当前 Agent stage、结果和 elapsed time |
| `RunEventStream` | AI message、tool、log、error、evidence |
| `AssetTile` | 4:3 预览、类型、状态、来源 |
| `AssetInspector` | prompt、provenance、license、review actions |
| `AssetRevisionStrip` | Previous 与 regenerated Candidate 的并列选择；接受前保留旧素材 |
| `GamePreviewFrame` | 稳定 16:9 preview 和 version controls |
| `CandidateBanner` | Candidate 状态 + “Playable remains Vx” |
| `TestCheckRow` | check、status、evidence、定位动作 |
| `VersionRow` | Version/Candidate 来源、状态、parent、action |
| `EvidenceLink` | Run/TestReport/Version/Resource 的可追溯跳转 |
| `ResourceUseRow` | resource → target project/run → usage |
| `RelevantExperience` | verified Experience 摘要和证据，不模拟 RAG |

### 5.3 Component Boundaries

- `StatusMark` 不包含业务动作。
- `DualTrackRail` 不决定 Candidate 是否发布，只展示 store 状态。
- `ArtifactFrame` 不保存独立副本，Structured/JSON/AI suggestion 必须指向同一 Artifact state。
- `AgentStageRail` 不使用聊天头像；Agent 身份用名称、工具权限和阶段表达。
- `AssetTile` 不承载完整 prompt/许可；详情进入固定 inspector，避免 tile 高度漂移。

## 6. Artifact 模式

GDD、GameSpec、Asset Set、Source File、TestReport、Version 和 Reusable Resource 都使用统一的
Artifact 语法。每个 Artifact 必须回答：**这是什么、来自哪里、当前能否修改、下一步由谁决定、
证据在哪里。**

### 6.1 Artifact Anatomy

```text
Artifact Header
├── Type icon + Name
├── State: Draft / Review / Verified / Failed / Archived
├── Source and updated time
└── Primary human action

Artifact Body
├── Content / preview / structured fields
└── Inline validation

Context Panel
├── AI suggestion or evidence
├── Provenance / parent / TestReport
└── Secondary actions
```

### 6.2 Three Modes

#### Author Mode

- 用于 GDD draft、GameSpec、源码。
- 支持直接编辑，显示 dirty/valid 状态。
- 主操作为 `Confirm` 或 `Save & build candidate`。
- AI 修改进入 Suggestion，不直接覆盖。

#### Review Mode

- 用于 AI suggestion、Asset review、Restore 和 Resource promotion。
- 同时展示当前内容与 proposed change/evidence。
- 主操作是人工 gate：Apply、Accept、Restore、Promote。
- Reject/Discard 明确保留原状态。

#### Evidence Mode

- 用于 TestReport、成功 Version、Reusable Resource。
- 默认只读，强调来源、验证、parent 和使用记录。
- 不用编辑控件伪装只读内容。
- 可以跳转到 source Artifact，但不能从证据视图暗中修改业务状态。

### 6.3 Artifact State Labels

| State | Icon | Color | Meaning |
|-------|------|-------|---------|
| Draft | Pencil | Blue | User/AI may still change it |
| Needs review | Eye | Orange | Human decision required |
| Confirmed | LockKeyhole | Approved teal | Human gate passed; edits require reconfirm |
| Candidate | FlaskConical | Orange | Not playable yet |
| Verified | BadgeCheck | Verified green | Evidence complete and reusable/playable |
| Failed | CircleX | Red | Gate blocked; stable result preserved |
| Archived | Archive | Neutral | Historical and read-only |

## 7. Agent 状态表现

### 7.1 Agent Is a Process, Not a Persona

- 不使用机器人头像、拟人气泡或“四个 Agent 群聊”。
- Agent 以 `Planning`, `Asset`, `Coding`, `Test` stage 和对应动作出现。
- 用户看到的是当前目标、完成事实、工具事件和结果，不展示模拟思维过程。
- Mock Prototype 统一显示 `Prototype · Mock runtime`，不声称真实 Claude/OpenGame 已运行。

### 7.2 Active Run Header

```text
Coding Agent  ·  Modifying from V2
Applying requested rule change                 02:14 elapsed   [Cancel]
━━━━━━━━━━━━━━━━━━━━━━━  58%
```

- stage 名称用 body strong，不使用 hero 字号。
- progress 只在能够确定时显示；未知进度使用阶段序列，不显示虚假百分比。
- Cancel 是 secondary/danger quiet action，需要确认但不做复杂 modal。

### 7.3 Event Stream

事件类型采用固定 icon 和格式：

| Type | Visual Treatment |
|------|------------------|
| AI message | Sparkles icon，正常文本，无聊天气泡 |
| Tool | Wrench icon，工具名 + 简短结果，可展开参数摘要 |
| Build log | Terminal icon，mono 文本，默认折叠 |
| Evidence | FileCheck icon，可跳转 Artifact |
| Usage | Gauge icon，低优先级 metadata |
| Error | CircleX icon，明确失败动作和可修复入口 |

### 7.4 Agent Completion

- `Planning complete` 后停在 GDD/GameSpec Review，不自动确认。
- `Assets generated` 后停在 Asset Review，不自动接受。
- `Coding complete` 只表示 Candidate ready，不表示成功。
- `Test PASS` 由平台门禁形成 Version；TestAgent 本身不显示“Published”。
- `Relevant Experience` 显示在 Coding context 中，包含 verified 标签和来源，不表现为模型“记忆”。

## 8. Candidate / Playable 表现

### 8.1 Dual Track Rail Contract

| Track | Always Shows | Action |
|-------|--------------|--------|
| Playable | Version number、PASS、更新时间 | Open preview |
| Candidate | Candidate label、stage/verdict、baseline | Open progress/report |

示例：

```text
PLAYABLE   V2  PASS · 已验证       14:32                    [打开试玩]
CANDIDATE  V3  FAILED · 测试失败   基于 V2                  [查看报告]
```

### 8.2 Candidate Rules

- 使用烧瓶 icon 与橙色/红色，不使用绿色 Version badge。
- 文案固定为 `V3 Candidate`，并在所有位置附 `Not published`。
- FAILED 时必须同时出现 `V2 remains playable`。
- Candidate 行允许查看、修复或回到代码；不提供 Preview as current。
- Candidate PASS 进入 publishing 时仍是 Candidate；Version 创建后才移动到 Playable 轨。

### 8.3 Playable Rules

- Playable 使用 BadgeCheck icon、绿色实线和明确 Version。
- Preview 总是读取 Playable，不根据“最新修改”切换。
- Restore V2 的运行期间 Playable 保持 V4；V5 PASS 后才切换 V5。
- Promotion 不改变 Playable。

### 8.4 Empty and First-failure State

尚无成功 Version 时：

```text
PLAYABLE   尚无已验证 Version
CANDIDATE  Initial Candidate · 构建失败          [查看错误]
```

不能使用空白 preview 暗示存在游戏；显示清楚的修复入口。

## 9. Asset Review 表现

### 9.1 Asset Grid

- Main Workspace 在 `≥1366px` 使用稳定 4 列网格，在 `1280–1365px` 使用 3 列；Asset tile 比例 `4:3`。
- tile 显示 preview、name、kind、source 和 status；文本行数固定，避免布局跳动。
- accepted：青色 check + `已接受`；pending：橙色 eye + `待审阅`；rejected：红色 x + `已拒绝`。
- 颜色边框仅作辅助，不能只靠整张图变色。

### 9.2 Asset Inspector

固定右侧 `344px`：

1. 大预览。
2. Name / kind / style。
3. Prompt。
4. Provenance / license。
5. Accept、Reject。
6. Reject 后显示自然语言 Regenerate composer。

接受/拒绝是明确命令按钮，不使用 toggle。Regenerate 使用 textarea + Sparkles icon 的
`重新生成素材`，不提供任意参数面板。

### 9.3 Regenerate Revision Review

- Regenerate 完成后不能立即覆盖原素材；Inspector 顶部显示 `Previous` 与 `New candidate` 并列预览。
- `AssetRevisionStrip` 固定保留上一版缩略图、新 Candidate、prompt 变化和生成时间。
- 用户选择 `接受新素材` 后，新 Candidate 才成为 accepted；选择 `保留原素材` 时丢弃新 Candidate，
  原素材状态保持不变。
- 若原素材已经 rejected，仍保留为历史 revision，不能从追溯信息中消失。
- Mock Prototype 的 Guide Mira 路径必须实际演示一次 Previous/New 比较。

### 9.4 Asset Set Gate

- 顶部显示 `4 accepted · 1 needs review`。
- `Accept asset set` 只在所有必需类型 accepted 后启用。
- 缺项用具体名称列出，不使用“Asset validation failed”。
- Placeholder 有 `Built-in fallback` source 标签；可以完成原型闭环，但来源保持可见。

### 9.5 Reusable Assets

- `Reusable assets` 是 Asset Studio 内的 tab，不另建选择器页面。
- Tile 增加 Library icon、source Version 和 verified provenance。
- 选择 `Guide Mira` 后显示 `Copy into project`，不用“Link”，避免暗示跨项目共享可写文件。
- ResourceUse 成功后显示 evidence link。

## 10. Test / Version 表现

### 10.1 TestReport

TestReport 是 Evidence Mode，不做红色错误大屏。

```text
V3 Candidate                         FAILED · 测试失败
1 项检查阻止发布                      V2 仍可试玩

✓ Build
✓ Page load
✓ Console errors
✓ Player movement
✓ Enemy loop
✓ Item collection
✓ NPC interaction
✕ Game outcome     Victory threshold cannot be reached
```

- 失败检查置顶摘要，但保留全部八项，证明测试完整。
- 每项使用 icon、状态、短消息和 evidence disclosure。
- `Ask AI to fix` 是唯一 primary action。
- `Open V2 preview` 是稳定保护入口，始终可见。
- 原始日志在 disclosure 中，不占据首屏。

### 10.2 Version History

使用紧凑表格/谱系行，而不是独立大卡片时间线：

| Record | Source | Parent / Relation | Test | Playable | Action |
|--------|--------|-------------------|------|----------|--------|
| V5 | Restore | Parent V2 | PASS | Current | Preview / Promote |
| V4 | AI repair | Parent V2 · Repairs V3 Candidate | PASS | Historical | Preview / Restore |
| V3 Candidate | User code | Based on V2 | FAILED | Never | Report / Fix |
| V2 | AI modify | Parent V1 | PASS | Historical | Preview / Restore |
| V1 | Initial | — | PASS | Historical | Preview |

- Version 与 Candidate 使用不同 icon 和背景，不用同一种 badge。
- 当前 playable 行有左侧绿色 `3px` marker，不整行铺绿色。
- Restore 打开 Dialog，说明会创建新 Version，不改写历史。
- Compare 使用分屏 diff，默认只对 parent 比较。
- Repair Version 除 `parentVersionId` 外必须显示 `repairsCandidateId` 关系；从 V4 可直接打开 V3
  FAILED TestReport，从 V3 也能跳转到最终修复它的 V4。

### 10.3 Version Detail

Context Panel 顺序固定：

1. Status and TestReport。
2. Source request / restore reason。
3. Parent Version。
4. Modified files。
5. GameSpec snapshot。
6. Preview artifact。
7. Reusable resource eligibility。

### 10.4 Promote Resources

- 作为 Version Evidence Mode 上的 primary/secondary command，进入独立 Dialog/Wizard。
- Template、Assets、Experience 三项使用 checkbox 多选；每项显示不同来源证据。
- 最终确认明确写出 `No Formal Skill will be modified`。
- 完成后进入 Resources，并显示 Template/Asset/Experience 的三条 ResourceUse-ready 记录。

## Visual Freeze Keyframes

以下三张关键画面的信息构图属于 v0.1 冻结内容。两人可以先确认并冻结本设计；Mock Prototype
实现后必须以 1440 × 900 和 1280 × 720 截图完成第一轮视觉验证。若实际画面无法满足构图和状态
要求，应进入新的设计评审，而不是在实现中静默偏离基线。

### K1. Build & Play · V2 Playable

```text
┌ Nav ┬ V2 PASS ━ Playable / No active Candidate ━━━━━━━━━━━━━━━━━━━━━━━┐
│     ├──────────────────────────────────────────────┬───────────────────┤
│     │                                              │  AI 修改游戏      │
│     │            16:9 Game Preview                 │  修改要求          │
│     │                                              │  [让 AI 修改]      │
│     ├──────────────────────────────────────────────┤  当前规则/NPC      │
│     │ Preview controls / Version evidence          │                   │
└─────┴──────────────────────────────────────────────┴───────────────────┘
```

验证重点：游戏本身是首屏主角；Dual Track 清楚但不抢 preview；AI composer 是工作工具，不是聊天首页。

### K2. TestReport · V3 FAILED, V2 Remains Playable

```text
┌ Nav ┬ PLAYABLE V2 PASS ━━━━━ CANDIDATE V3 FAILED ━━━━━━━━━━━━━━━━━━━━━┐
│     ├──────────────────────────────────────────────┬───────────────────┤
│     │  FAILED · 1 check blocked publication        │ Candidate: V3     │
│     │  ✓ Build              ✓ NPC interaction      │ Based on: V2      │
│     │  ✓ Player movement    ✕ Game outcome         │ V2 仍可试玩       │
│     │                                              │ [打开 V2]         │
│     │  Evidence disclosure                         │ [让 AI 修复]      │
└─────┴──────────────────────────────────────────────┴───────────────────┘
```

验证重点：失败不形成红色大屏；`V2 仍可试玩` 与 `让 AI 修复` 无需滚动即可看见；V4 能追溯
`Repairs V3 Candidate`。

### K3. Asset Studio · Regenerate Revision Review

```text
┌ Nav ┬ GDD ✓ ─ GameSpec ✓ ─ Assets ● ─ Game ○ ────────────────────────┐
│     ├──────────────────────────────────────────────┬───────────────────┤
│     │ [Player] [Enemy] [Item] [NPC]                │ Guide Mira        │
│     │ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐         │ Previous | New    │
│     │ │asset │ │asset │ │asset │ │asset │         │ [previews]        │
│     │ └──────┘ └──────┘ └──────┘ └──────┘         │ Prompt / source   │
│     │ 4 accepted · 1 needs review                  │ [保留原素材]      │
│     │                                              │ [接受新素材]      │
└─────┴──────────────────────────────────────────────┴───────────────────┘
```

验证重点：revision 对比清晰；素材 tile 尺寸稳定；accepted 使用 approved teal，不冒充系统 PASS。

### Keyframe Width Acceptance

- 1440px：完整导航、固定 Context Panel、Main Workspace 无遮挡。
- 1280px：56px icon navigation；Context Panel 默认关闭，打开时 overlay；Asset grid 为 3 列。
- 两个宽度下主操作、Dual Track、失败保护文案和素材 review action 均不截断、不重叠。
- Prototype Review 证据需附六张截图：3 个 keyframe × 2 个 viewport。

## Freeze Checklist

两名开发者需要逐项确认：

- [ ] 接受 `Verified Workshop` 作为唯一视觉方向。
- [ ] 接受 Dual Track Rail 作为产品 signature 和核心状态表达。
- [ ] 接受宽屏 216px 导航 + Main Workspace + 344px Context Panel，以及 1280px 折叠规则。
- [ ] 接受项目/设计/素材/构建与试玩/代码/版本/资源导航结构。
- [ ] 接受本文件的颜色、字体、间距、圆角和状态 token。
- [ ] 接受 approved teal 与 verified green 分离，Human Gate 不冒充系统 PASS。
- [ ] 接受 Artifact 的 Author/Review/Evidence 三种模式。
- [ ] 接受 Agent 以 stage/event 表现，不使用拟人群聊或思维过程。
- [ ] 接受 V3 显示为 `V3 Candidate · Not published`，并始终标注稳定 Playable。
- [ ] 接受 Asset Grid + 固定 Inspector 的审阅模式。
- [ ] 接受 Regenerate 使用 Previous/New Candidate revision review，不覆盖旧素材。
- [ ] 接受 TestReport 八项检查与表格式 Version History。
- [ ] 接受 Repair Version 显式展示 `Repairs Candidate` 双向证据关系。
- [ ] 接受 Reusable Knowledge 通过人工 promotion 和 evidence link 进入产品。
- [ ] 接受 Desktop-only 原型，但正式前端仍需保持 keyboard focus 与 reduced motion 基线。
- [ ] 接受 Prototype Review 必须提交 1440px 与 1280px 的六张 keyframe 截图进行验证。

## Frozen Decisions and Deferred Questions

### v0.1 确认后冻结

- 视觉主题、布局骨架、导航命名、token、基础组件和状态颜色。
- 1280px 使用 icon rail + overlay Context Panel，不同时硬塞三栏。
- 中文优先文案、本地字体资源以及 approved/verified 分离。
- Artifact 三模式。
- Agent、Candidate/Playable、Asset Review、TestReport、Version History 的表现规则。
- 不使用紫色渐变、深色电竞主题、营销 hero、聊天机器人首页或卡片套卡片。

### Prototype Review 后再决定

- GDD 与 GameSpec 是否最终合并为同一 route 下的 tabs；视觉模式不变。
- AI suggestion 是否从整体 Apply/Discard 升级为逐块接受。
- Project Beta 是否在 Mock Prototype 中继续生成到可玩 Version。
- 正式前端是否允许用户折叠主导航并记住偏好。
- Resource Retire 是否进入正式 V2 首屏操作。

这些问题不阻塞 v0.1 作为原型和正式前端设计基线，也不改变本文件待确认的核心状态语义。
