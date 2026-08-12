# 项目状态驱动的完整生命周期 — 设计文档

日期：2026-08-12
状态：已冻结（用户批准 + 5 条补充约束）
范围：`ai-cowork-game/frontend`

## 背景

代码评审发现 8 条问题（P0×3、P1×3、P2×2）：资源复用推荐只由 `?screen=resource-reuse` 硬编码触发；离开 K02 Workspace 销毁全部开发状态；Projects 页不是项目列表；Resource Review 保存竞态产生永久 `saving`；资源库预装全部候选导致保存无新增感；候选为全局一次性 fixture 不按 Release 分批；版本模型存在重复真相源；Workspace 视觉内容与农场 fixture 耦合。

目标：修复全部 8 条，并演进为**单一项目状态驱动的完整生命周期**：

`Idea → Game Design → GameSpec → Build → Playable v1 → Change → Playable v2 → Version → Publish → Resource Review → 我的资源 → （新项目复用已保存资源）`

## 架构总览

新增模块级 reactive 单例 store（不引 Pinia，与现有代码风格一致）。所有跨页面生命周期的业务状态与业务异步流程归 store 所有；Vue 组件只持有纯 UI 的瞬时状态。

```
src/stores/projectStore.ts      — ProjectSession 模型、项目列表、资源库、业务 actions + store-owned timers
src/stores/resourceMatching.ts  — 结构化 GameSpec 字段的 deterministic signal matching
src/stores/demoSeeds.ts         — ?screen= 入口的 store 播种（替代 URL 直开组件状态）
```

## 1. ProjectSession 模型

```ts
type PlayableVersionRecord = {
  version: number              // 1-based，单调递增
  name: string
  summary: string
  reason: 'initial' | 'change' | 'restore'
  restoredFrom?: number        // 仅 reason === 'restore'
  basedOnDesign: number
  basedOnSpec: number
  createdAt: number
}

type ProjectSession = {
  id: string
  createdAt: number
  updatedAt: number            // 每个 store action 更新，供 Projects 列表展示"最近活跃"

  design: ConfirmedGameDesign
  spec: GameSpecModel

  // 版本真相源（唯一）
  designVersion: number        // 新建 = 1
  specVersion: number          // 新建 = 1
  playableVersions: PlayableVersionRecord[]
  playableVersion: number      // 指向 playableVersions 中最新 record 的 version
  currentRelease: ReleaseRecord | null
  releaseCount: number

  // 原 K02 local state，全部上移
  phase: WorkspacePhase
  activeTab: ArtifactTab
  messages: CoworkMessage[]
  changePlan: ChangePlan | null
  releasePhase: ReleasePhase
  releaseDraft: ReleaseDraft
  versionHistoryOpen: boolean
  releaseReviewOpen: boolean
  releaseDetailOpen: boolean
  reuseDrawerOpen: boolean
  reuseFeedback: boolean
  relationshipSnapshot: RelationshipDraft | null
  pendingContext: SpecContext | null
  selectedContext: SpecContext | null
  resourceBridgeAcknowledged: boolean

  // 资源复用决策（见 §3）
  reuseDecisions: Record<string, 'dismissed' | 'used'>
  reuseSpecVersion: number     // 决策发生时所属的 specVersion

  // 资源候选批次（见 §4）
  resourceBatches: Record<string, ResourceCandidate[]>  // releaseId → 批次
}
```

Store 根状态：

```ts
{
  projects: ProjectSession[]
  activeProjectId: string | null
  savedResources: ResourceCandidate[]   // 全局资源库，启动时为空（demo seed 除外）
}
```

`K02ProjectWorkspace` 接收 `session` prop，内部用 `toRefs(session)` 将字段当本地 ref 使用——对现有交互逻辑是机械替换，不重写。`v-if` 卸载 K02 不再丢失任何状态（修 finding 2）。

## 2. Store 接管业务 timer（约束 1）

以下模拟异步流程全部由 projectStore action 推进，timer 归 store 持有（`Map<projectId, timeoutId>` 注册表，同一项目新 action 启动时清理旧 timer）：

- GameSpec generation（`startGeneration`，1250ms → `review`）
- Build timeline（`advanceBuild` 序列）
- Change timeline（`advanceChange` 序列）
- Publish（`publishRelease`，900ms）
- Resource candidate 保存（`saveCandidate`，420ms，直接写 store 批次）

**禁止**已卸载组件创建的 timer closure 继续修改 store。组件卸载时不需要清理 store timer；业务在离开 Workspace 后继续推进（例如离开 Build 页面去我的资源，回来后 Build 已完成）。

边界：纯 UI 瞬时反馈 timer（如 `reuseFeedback` 900ms 高亮闪烁、模板卡片 flash）仍归组件所有，因为它们不修改业务状态。

错误注入参数（`specError` / `buildError` / `scopeError` / `publishError` / `kickoffError`）保留，作为 seed/调试参数传入 store action，不再由组件读 URL。

## 3. 资源复用：真实触发（finding 1 + 约束 2、4）

### 匹配器 `resourceMatching.ts`

```ts
type ResourceMatchSignals = {
  section: SpecContext['key']   // 目前只有 'characters'
  signals: string[]             // 如 ['委托', '好感', '关系', 'NPC']
}

function matchResourcesToSpec(spec: GameSpecModel, resources: ResourceCandidate[]): Map<resourceId, SpecContext['key']>
```

- 匹配基于**结构化 GameSpec 字段**做 deterministic matching：`spec.characters` 的各字符串字段（`primaryNpcs` / `relationshipGrowth` / `favorRules` / `relationshipEvents` / `requestRewards` / `npcBehaviors[]`）与 `spec.gameplay.actions[]`、`spec.rules.progression[]` 中属于该 section 语义的字段。
- **不**对整个 spec 做 stringify，**不**依赖任何 DOM 文案。
- 命中规则：某资源 ≥2 个 signal 出现在其 section 对应的结构化字段中 → 推荐。
- 信号定义随资源 fixture 数据声明（数据驱动，新增资源不需改 matcher 代码）。

### 触发时机

GameSpec generation 完成进入 `review` 时（store 的 `startGeneration` 完成分支内）执行匹配，结果写入 session；推荐渲染在「NPC 与关系」Section 内。Idea / Game Design / Build 之后不首次弹出。

农场项目真实链路生成的 spec 含「NPC 委托、好感成长、关系事件」→ 自动命中 `relationship-system`，无需 URL flag。

### dismiss 语义（约束 2）

- `dismissed` 写入 `session.reuseDecisions`，**跨组件卸载/挂载保持**。
- 决策按 `specVersion` 作用域生效：渲染推荐的条件是 `reuseSpecVersion === specVersion` 且 `reuseDecisions[id]` 不存在。在当前 GameSpec Draft/Review 周期内，普通 Section revision（`applyRevision`）**不**重新弹出同一推荐。
- 仅当进入**新的 GameSpec version**（`specVersion` 递增时 store 清空 `reuseDecisions` 并重置 `reuseSpecVersion`，未来流程）或**明确重置决策**（"取消使用"仅作用于 `used` 态）时重新评估。

### 使用资源的内容适配（部分 finding 8）

`useRelationshipResource` 不再硬编码咖啡店文案，改从资源的 `configurableFields`（好感阈值 `30 / 50 / 80`、任务奖励 `好感 +5`）+ 当前 spec 的 NPC 名派生写入 `spec.characters`；`relationshipSnapshot` 保留以支持"取消使用"。

## 4. 资源生命周期（findings 4、5、6）

### 启动为空

`savedResources` 初始为 `[]`。真实链路：首次 Release → Review 保存 → 我的资源 0 → 1，有明确新增感（修 finding 5）。`MyResources` 增加全空态文案（区别于"筛选无结果"态）。

### 按 Release 生成批次（finding 6）

`publishRelease` 成功时，store 调用 `extractCandidatesFromRelease(session, release)`：

- provenance 全部取真实值：`projectName = design.projectTitle`、`releaseVersion = Release v{n}`、`playableVersion = Playable v{n}`、`gameSpecVersion = GameSpec v{specVersion}`。
- 已在 `savedResources` 中的资源 id、以及在历史批次中已被 `ignored` 的资源 id，均不再进入新批次。
- 提取规则是确定性的：候选模板与 spec/changePlan 内容对应（如关系增强类 change → `favor-hud` 类候选）；若过滤后无任何新候选，则生成一项由 changePlan 摘要派生的"本版本迭代内容"通用候选，保证每个 Release 的批次非空。
- 每个新 Release 得到自己的批次，批次写入 `session.resourceBatches[release.id]`，处理状态（pending/saving/saved/ignored）随批次持久在 session 中，再次进入 Review 继续处理而非重置。

### 保存竞态（finding 4）

Review 页不再克隆 candidates 到组件本地，直接读写 store 批次；420ms timer 为 store-owned（约束 1），组件卸载不影响 `saving → saved` 落定。`pendingResourceCount` 改为从 active project 最新批次的 computed 派生，不再由 App.vue 手工同步。

## 5. 版本模型统一（finding 7 + 约束 3）

- 新建项目 `designVersion = 1`、`specVersion = 1`；Release draft 的 `basedOnPlayable / basedOnGameDesign / basedOnGameSpec` 全部读 session 实际值；首个 Release 名称 `{项目名} · First Release`。
- `playable_ready` → push `PlayableVersionRecord{ version:1, reason:'initial', … }`；`playable_v2_ready` → push `{ version:2, reason:'change', name/summary 来自 changePlan, … }`。
- **Restore**（约束 3）：版本历史面板提供恢复操作（替换现有"本阶段不提供恢复操作"注释）。Restore **不**回退指针，而是 push 新 record：`{ version: 当前最大+1, reason:'restore', restoredFrom: 目标版本, name/summary 复制自目标版本 }`，`playableVersion` 指向新 record。旧 record 不被修改。`playableVersions` 由此成为版本历史的唯一真相源。
- `VersionHistoryDrawer` 改为 props 驱动（`versions: PlayableVersionRecord[]`、`designVersion`、`specVersion`），删除全部静态记录；恢复操作 emit 给 store action。

## 6. Projects 真实列表（finding 3 + 约束 5）

K01 页面保留创建区，新增「我的项目」列表（位于创建区之上）：

- 每项显示：项目名、阶段徽章（`GameSpec` / `Building` / `Playable v{n}` / `Released v{n}`，从 session 字段派生）、最近活跃（`updatedAt` 相对时间）。
- 点击 → `store.openProject(id)` → Workspace 恢复该 session。
- 创建新项目 → `store.createProject(design)` → 新 session 进入 Workspace。
- Workspace 头部「Projects」返回列表，session 完整保留。

## 7. Demo 入口改为状态播种

`App.vue` 启动时解析 `?screen=`，调用 `demoSeeds.ts` 中对应 seed 函数，全部产出 store 状态而非组件 flag：

| 入口 | 播种内容 |
|---|---|
| `gamespec` / `build` / `change` / `publish` | 农场项目 + session 字段直接置为对应阶段（等价今天行为，含对应 timer 是否自动推进由 seed 决定） |
| `resource-reuse` | `savedResources` 预置 `relationship-system`（provenance 标注来自上一个农场项目）+ 咖啡店项目置于 gamespec generation → 推荐由 matcher 真实触发 |
| `resources` | 农场项目 + 已发布 Release v1 + 待处理候选批次，直接进入 Review |
| `my-resources` | `savedResources` 预置 3 项已保存资源 |
| 无参数 | 空库 + 空项目列表，完整真实链路 |

## 8. 配套解耦（finding 8）

- `kickoffFixtures` 新增 `coffeeScenario`（关键词 `咖啡|coffee` 命中，优先级低于 farm 高于 generic），含 coreQuestion / followUps / buildSummary，使「咖啡店 Idea → 真实创建 → GameSpec 触发复用推荐」成为真实可达链路——复用闭环：第一个农场项目沉淀 `relationship-system`，第二个咖啡店项目复用它。
- `BuildPreview` 增加 `session` 派生 props：项目名、NPC 名、能力列表从 `design` / `spec` / 当前 phase 派生；农场 preview 图仅农场场景使用，其他场景用泛化视觉占位与文案。
- `ResourceReviewWorkspace` 头部项目名从 session 读取。
- `resourceFixtures.ts` 从"静态数据"改为"生成函数"：`createResourceCandidates(session, release)` 等，静态文案保留为模板。

## 文件变更清单

**新增**
- `src/stores/projectStore.ts`
- `src/stores/resourceMatching.ts`
- `src/stores/demoSeeds.ts`

**修改**
- `src/App.vue` — 改为 store 驱动的薄壳；surface 路由；删除 fixture 直引
- `src/screens/K02ProjectWorkspace.vue` — local state → `toRefs(session)`；业务 timer 调用改为 store action
- `src/screens/K01CreateProject.vue` — 新增项目列表
- `src/screens/ResourceReviewWorkspace.vue` — 直接读写 store 批次；头部项目名动态化
- `src/screens/MyResources.vue` — 全空态
- `src/components/workspace/VersionHistoryDrawer.vue` — props 驱动 + restore
- `src/components/workspace/BuildPreview.vue` — 内容从 session 派生
- `src/components/workspace/gameSpecFixture.ts` — 候选人/provenance 生成函数化
- `src/components/resources/resourceFixtures.ts` — 生成函数化 + 匹配信号声明
- `src/components/kickoff/kickoffFixtures.ts` — 新增 coffeeScenario
- `src/components/workspace/workspaceTypes.ts` — `PlayableVersionRecord` 等类型

## 错误处理

- 所有 store action 的 timer 在推进前检查 session 仍存在（项目可能被忽略的场景暂不出现，但保持防御）。
- 错误注入路径（specError 等）行为与现状一致：首次触发进入错误态，重试后正常。
- Restore 目标版本不存在时 action 为 no-op。

## 测试与验证

1. `vue-tsc -b && vite build` 通过。
2. 浏览器真实链路 ①：空库启动 → Idea（农场）→ Game Design → GameSpec（无推荐，因为库为空）→ Build → Playable v1 → Change → Playable v2 → 版本历史（v1/v2 均为真实版本号，基于 Design v1 · GameSpec v1）→ Publish Release v1 → Resource Review（批次 provenance 真实）→ 保存 `relationship-system` → 我的资源 0→1。
3. 浏览器真实链路 ②：新建咖啡店 Idea → Game Design → GameSpec「NPC 与关系」Section 出现 `relationship-system` 推荐 → 使用 → spec.characters 更新为资源参数化内容 → dismiss/取消使用行为符合 §3。
4. 状态保持：Build 进行中离开到我的资源 → 返回后 Build 已完成且可继续；Review 保存中离开 → 返回后状态落定无永久 `saving`。
5. Projects 列表：两个项目并存，阶段徽章与最近活跃正确，点击恢复各自 session。
6. Restore：v2 状态恢复 v1 → 产生 v3（reason: restore, restoredFrom: 1），历史面板显示三条记录。
7. dismiss 持久：dismiss 推荐 → 离开/返回 Workspace → 不再出现；普通 revision 后不重新弹出。
8. Demo 入口逐个冒烟（`?screen=` 各值），控制台无应用自身 warning/error。
