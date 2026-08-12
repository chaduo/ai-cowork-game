# Project Lifecycle State Store Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** 将 AI Cowork Game 前端从“页面 fixture + 组件本地生命周期”重构为“项目状态驱动的完整前端生命周期”，让项目、版本、Release、资源沉淀、跨项目资源复用和 Demo 入口共享同一套状态模型。

**Architecture:** 使用模块级 Vue `reactive` 单例 store，不引 Pinia。跨页面业务状态和跨页面异步流程归 `projectStore`；Drawer、Modal、当前 Tab、短暂高亮等纯 UI 状态继续留在组件。`playableVersions[]` 与 `releases[]` 分别作为唯一真相源；URL demo 入口只负责 seed store。

**Tech Stack:** Vue 3、TypeScript、Vite、现有组件与 CSS；不新增状态管理库、Router、推荐或后端依赖。

## Global Constraints

- `ProjectSession` 从 **Game Design Confirmed** 开始；Creative Kickoff 仍是创建前 Draft。
- 不引 Pinia / Vue Router / 新测试框架。
- 不重写已有 Workspace 交互，只收敛状态所有权与数据源。
- 业务状态只通过 `projectStore` actions 修改；组件只能直接修改纯 UI 状态。
- Store timer 按 `projectId + jobKey` 隔离。
- `playableVersions[]` 是 Playable 唯一真相源；不持久化第二份 `playableVersion`。
- `releases[]` 是 Release 唯一真相源；不持久化 `currentRelease/releaseCount`。
- Restore 必须复制目标 Playable snapshot。
- Release 允许空资源批次；禁止制造兜底 Candidate。
- Matcher 基于结构化 GameSpec 字段；禁止 DOM 文案或整个 spec stringify。
- 复用参数使用 machine-readable `reuseDefaults`，禁止解析 `configurableFields`。
- dismiss 在当前 `specVersion` 周期内持续有效；普通 revision 不重新推荐。
- 无 URL 参数时：项目列表为空、资源库为空，可从真实 Idea 链路完整跑通。
- `?screen=` 只 seed store；错误参数只作为 debug config 传给 store action。
- 每个任务完成后运行：`cd frontend && npx vue-tsc -b && npx vite build`。

---

## Target State Ownership

### Store / ProjectSession

```ts
export type ProjectSession = {
  id: string
  createdAt: number
  updatedAt: number
  design: ConfirmedGameDesign
  spec: GameSpecModel
  designVersion: number
  specVersion: number
  playableVersions: PlayableVersionRecord[]
  releases: ReleaseRecord[]
  phase: WorkspacePhase
  messages: CoworkMessage[]
  changePlan: ChangePlan | null
  releasePhase: ReleasePhase
  releaseDraft: ReleaseDraft
  pendingContext: SpecContext | null
  reuseDecisions: Record<string, 'dismissed' | 'used'>
  reuseSpecVersion: number
  matchedResources: Record<string, SpecContext['key']>
  relationshipSnapshot: RelationshipDraft | null
  resourceBridgeAcknowledged: boolean
  resourceBatches: Record<string, ResourceBatchItem[]>
}
```

### Component-local UI state

```ts
activeTab
selectedContext
versionHistoryOpen
releaseReviewOpen
releaseDetailOpen
reuseDrawerOpen
reuseFeedback
```

### Store-derived values

```ts
getCurrentPlayable(session)
getCurrentRelease(session)
getPendingResourceCount(session)
getProjectStageLabel(session)
```

---

# Task 1: 领域模型与 Store 骨架

**Files**
- Create `frontend/src/stores/projectStore.ts`
- Modify `frontend/src/components/workspace/workspaceTypes.ts`
- Modify `frontend/src/components/resources/resourceTypes.ts`
- Modify `frontend/src/components/workspace/gameSpecFixture.ts`

**Types**

```ts
export type PlayableSnapshot = {
  projectTitle: string
  npcNames: string[]
  capabilities: string[]
  previewVariant: 'farm' | 'coffee' | 'generic'
  relationshipSummary: string
}

export type PlayableVersionRecord = {
  version: number
  name: string
  summary: string
  reason: 'initial' | 'change' | 'restore'
  restoredFrom?: number
  basedOnDesign: number
  basedOnSpec: number
  createdAt: number
  snapshot: PlayableSnapshot
}

export type ResourceBatchState = 'pending' | 'saving' | 'saved' | 'ignored'
export type ResourceBatchItem = { candidate: ResourceCandidate; state: ResourceBatchState }
export type RelationshipDraft = {
  relationshipGrowth: string
  favorRules: string
  relationshipEvents: string
  requestRewards: string
}
export type ResourceMatchSignals = { section: SpecContext['key']; signals: string[] }
export type RelationshipReuseDefaults = {
  favorMin: number
  favorMax: number
  thresholds: number[]
  requestReward: number
  importantEventReward: number
}
```

Extend `ResourceCandidate` additively:

```ts
matchSignals?: ResourceMatchSignals
reuseDefaults?: RelationshipReuseDefaults
```

Add to `GameSpecModel.characters` without removing existing fields:

```ts
relationshipGrowth: string
favorRules: string
relationshipEvents: string
requestRewards: string
```

Steps:
- [ ] Add the types above.
- [ ] Update `createGameSpecFixture()` to always populate the four structured relationship fields.
- [ ] Create `projectStore = reactive({ projects: [], activeProjectId: null, savedResources: [] })`.
- [ ] Add `getProject/getActiveProject/getCurrentPlayable/getCurrentRelease/getPendingResourceCount`.
- [ ] Add `createProjectSession/createProject/openProject/touchProject`.
- [ ] Initialize new sessions with `designVersion=1`, `specVersion=1`, empty versions/releases/resources, `phase='generating'`.
- [ ] Verify build/typecheck.
- [ ] Commit: `refactor: add project session domain model`.

---

# Task 2: Store 接管业务 Actions 与 Timers

**Files**
- Modify `frontend/src/stores/projectStore.ts`
- Modify `frontend/src/screens/K02ProjectWorkspace.vue`

Timer model:

```ts
type TimerJobKey =
  | 'generation'
  | 'build'
  | 'change'
  | 'publish'
  | `resource-save:${string}:${string}`

const timers = new Map<string, Map<TimerJobKey, number>>()
```

Public actions:

```ts
startGeneration(projectId)
requestSpecRevision(projectId, context, text)
applySpecRevision(projectId)
requestSpecConfirmation(projectId)
confirmSpecAndStartBuild(projectId)
retryBuild(projectId)
requestChange(projectId, source, request?)
cancelChange(projectId)
applyControlledChange(projectId)
retryScopeViolation(projectId)
```

Steps:
- [ ] Implement `scheduleJob/clearJob` with project + job isolation.
- [ ] Move 1250ms GameSpec generation into store.
- [ ] Move revision state transitions/mutations into store.
- [ ] Move Build timeline into store.
- [ ] Move Change timeline into store.
- [ ] Remove component-owned business timers and `onBeforeUnmount(clearTimer)`.
- [ ] Keep `activeTab/selectedContext/drawers/modals/reuseFeedback` local.
- [ ] Manual verify: leave Workspace during Build, return later, phase progressed.
- [ ] Commit: `refactor: move workspace lifecycle into project store`.

---

# Task 3: Playable / Release 唯一真相源与真实 Restore

**Files**
- Modify `frontend/src/stores/projectStore.ts`
- Modify `frontend/src/components/workspace/VersionHistoryDrawer.vue`
- Modify `frontend/src/components/workspace/BuildPreview.vue`
- Modify `frontend/src/screens/K02ProjectWorkspace.vue`
- Modify `frontend/src/components/workspace/releaseTypes.ts`

Interfaces:

```ts
createPlayableSnapshot(session)
appendPlayableVersion(projectId, { name, summary, reason })
restorePlayable(projectId, targetVersion)
createReleaseDraftForProject(projectId)
publishRelease(projectId)
```

Steps:
- [ ] `createPlayableSnapshot()` derives title/NPC/capabilities/previewVariant/relationshipSummary from current project/spec.
- [ ] First Build success appends v1 `{ reason:'initial' }`.
- [ ] Controlled Change success appends next version `{ reason:'change' }`.
- [ ] Remove persisted `playableVersion`; derive current version from `playableVersions.at(-1)`.
- [ ] Restore finds target version, clones its snapshot, appends a new version `{ reason:'restore', restoredFrom: target.version }`.
- [ ] Convert VersionHistoryDrawer to props-driven `versions/designVersion/specVersion` + `restore` emit.
- [ ] BuildPreview consumes current Playable snapshot; no `playableVersion===2` logic.
- [ ] Replace `currentRelease/releaseCount` with `releases[]`.
- [ ] `createReleaseDraftForProject()` derives basedOn values from session truth.
- [ ] Manual verify v1 → v2 → restore v1 → v3, v3 preview matches v1 snapshot and v2 remains.
- [ ] Commit: `refactor: unify playable and release history`.

---

# Task 4: Release-scoped Resource Batches 与安全保存

**Files**
- Modify `frontend/src/stores/projectStore.ts`
- Modify `frontend/src/components/resources/resourceFixtures.ts`
- Modify `frontend/src/screens/ResourceReviewWorkspace.vue`
- Modify `frontend/src/screens/MyResources.vue`
- Modify `frontend/src/App.vue`

Interfaces:

```ts
createResourceCandidates(session, release)
extractCandidatesForRelease(projectId, releaseId)
saveCandidate(projectId, releaseId, candidateId)
ignoreCandidate(projectId, releaseId, candidateId)
```

Steps:
- [ ] Convert static candidate instances to generator functions returning fresh objects.
- [ ] Provenance must use real project/release/playable/spec versions.
- [ ] Allow `[]` candidate batches; remove generic fallback candidate.
- [ ] Filter globally saved candidates and historically ignored same-project candidates.
- [ ] Publish success pushes Release then creates `resourceBatches[release.id]`.
- [ ] Candidate save uses `resource-save:${releaseId}:${candidateId}` store timer.
- [ ] ResourceReview reads batch directly from session; no local clone.
- [ ] Empty batch copy: `这次发布没有发现需要单独保存的新资源。`
- [ ] Pending count is derived from latest batch.
- [ ] My Resources true empty state differs from search no-result state.
- [ ] Verify leaving during 420ms save cannot leave permanent `saving`.
- [ ] Commit: `feat: persist release resource batches`.

---

# Task 5: GameSpec 真实资源匹配与复用

**Files**
- Create `frontend/src/stores/resourceMatching.ts`
- Modify `frontend/src/stores/projectStore.ts`
- Modify `frontend/src/components/resources/resourceFixtures.ts`
- Modify `frontend/src/components/workspace/GameSpecDocument.vue`
- Modify `frontend/src/components/workspace/ResourceReuseRecommendation.vue`
- Modify `frontend/src/components/workspace/ResourceReuseDrawer.vue`
- Modify `frontend/src/components/workspace/workspaceTypes.ts`

Interfaces:

```ts
matchResourcesToSpec(spec, resources)
refreshResourceMatches(projectId)
dismissResourceRecommendation(projectId, resourceId)
useRelationshipResource(projectId, resourceId)
cancelRelationshipResource(projectId, resourceId)
```

Relationship resource machine data:

```ts
matchSignals: { section:'characters', signals:['委托','好感','关系','NPC'] }
reuseDefaults: {
  favorMin:0,
  favorMax:100,
  thresholds:[30,50,80],
  requestReward:5,
  importantEventReward:10,
}
```

Steps:
- [ ] Matcher only reads explicitly mapped structured relationship fields.
- [ ] Match when >=2 signals hit.
- [ ] Successful generation calls `refreshResourceMatches(projectId)`.
- [ ] Visibility respects current `specVersion` + `reuseDecisions`.
- [ ] Ordinary revision does not clear dismiss.
- [ ] `useRelationshipResource()` stores only relationship snapshot and applies `reuseDefaults`.
- [ ] No Lucy/farm hard-coded content in new project.
- [ ] `cancelRelationshipResource()` restores only relationship fields; other sections stay untouched.
- [ ] GameSpec model never stores resource workflow metadata.
- [ ] Verify empty library => no recommendation; saved relationship resource => real recommendation.
- [ ] Commit: `feat: match saved resources to gamespec`.

---

# Task 6: Projects 真实列表与 App 薄壳

**Files**
- Modify `frontend/src/App.vue`
- Modify `frontend/src/screens/K01CreateProject.vue`
- Modify `frontend/src/screens/K02ProjectWorkspace.vue`
- Modify `frontend/src/screens/MyResources.vue`
- Modify `frontend/src/style.css`

Steps:
- [ ] App stops owning project/resource fixtures; reads store only.
- [ ] Keep only surface UI state in App: `projects/workspace/resource-review/my-resources`.
- [ ] Kickoff confirm calls `createProject(design)` then opens Workspace.
- [ ] Add “我的项目” list above create area.
- [ ] Each project shows project name, derived stage, relative updatedAt.
- [ ] Stage derivation order: Released → Playable → Building → GameSpec.
- [ ] Clicking project calls `openProject(id)` and restores its session.
- [ ] Workspace “Projects” only changes App surface; does not reset session.
- [ ] My Resources reads global `savedResources` directly.
- [ ] Verify two projects coexist and restore independently.
- [ ] Commit: `feat: add persistent project list`.

---

# Task 7: Demo URL 改为 Store Seeds

**Files**
- Create `frontend/src/stores/demoSeeds.ts`
- Modify `frontend/src/App.vue`
- Modify `frontend/src/stores/projectStore.ts`
- Modify `frontend/src/screens/K02ProjectWorkspace.vue`

Interfaces:

```ts
type DemoSeedName = 'gamespec'|'build'|'change'|'publish'|'resource-reuse'|'resources'|'my-resources'
type DemoErrorFlags = {
  specError:boolean
  buildError:boolean
  scopeError:boolean
  publishError:boolean
  kickoffError:boolean
}
seedDemo(name, flags): AppSurface
```

Steps:
- [ ] Parse URL only in App/demo bootstrap.
- [ ] K02 and child components stop reading `window.location.search`.
- [ ] Store debug flags in runtime config map, not GameSpec.
- [ ] Implement seeds for gamespec/build/change/publish using real ProjectSession shapes.
- [ ] `resource-reuse` seeds saved relationship resource + coffee project then calls real generation/matcher; never directly writes matchedResources.
- [ ] `resources` seeds a real project/release/batch.
- [ ] `my-resources` seeds global saved resource library only.
- [ ] No-param startup remains empty.
- [ ] Smoke all `?screen=` values with no app console errors.
- [ ] Commit: `refactor: seed demo routes through project store`.

---

# Task 8: 新增真实 Coffee Kickoff 场景

**Files**
- Modify `frontend/src/components/kickoff/kickoffFixtures.ts`
- Modify `frontend/src/components/workspace/gameSpecFixture.ts`
- Modify `frontend/src/components/workspace/workspaceTypes.ts`

Steps:
- [ ] Add `/咖啡|coffee/i` scenario matching: farm-specific > coffee > generic.
- [ ] Add coffee core question using existing Kickoff interaction pattern.
- [ ] Add follow-ups/build summary with two NPCs + relationship growth intent + first playable scope.
- [ ] `createGameSpecFixture()` derives coffee structured relationship fields containing >=2 matcher signals.
- [ ] Verify no-param real flow: coffee idea → Kickoff → Confirm Design → GameSpec → recommendation when resource exists.
- [ ] Commit: `feat: add coffee kickoff scenario`.

---

# Task 9: BuildPreview 与农场 Fixture 解耦

**Files**
- Modify `frontend/src/components/workspace/BuildPreview.vue`
- Modify `frontend/src/screens/K02ProjectWorkspace.vue`
- Modify `frontend/src/components/workspace/buildTypes.ts` if needed
- Modify `frontend/src/style.css`

Preferred props:

```ts
phase
playable: PlayableVersionRecord | null
release: ReleaseRecord | null
resourceBridgeAcknowledged
resourcePendingCount
```

Steps:
- [ ] Project title from snapshot/session, not hard-coded.
- [ ] NPC/capabilities from snapshot.
- [ ] farm variant uses existing farm image.
- [ ] coffee variant uses neutral coffee-specific CSS/visual placeholder, not farm image.
- [ ] generic uses neutral prototype preview.
- [ ] Restore visibly changes Preview because snapshot changed.
- [ ] ResourceReview/Release header project names become dynamic.
- [ ] Run `grep -R "多代田园物语\|Lucy" frontend/src/screens frontend/src/components/workspace -n` and remove any match acting as global Workspace truth.
- [ ] Commit: `refactor: derive preview content from playable snapshot`.

---

# Task 10: Release → Review → 我的资源真实闭环

**Files**
- Modify `frontend/src/screens/K02ProjectWorkspace.vue`
- Modify `frontend/src/screens/ResourceReviewWorkspace.vue`
- Modify `frontend/src/screens/MyResources.vue`
- Modify `frontend/src/App.vue`
- Modify `frontend/src/stores/projectStore.ts`

Steps:
- [ ] Publish success UI reads `getCurrentRelease(session)`.
- [ ] Review CTA opens the latest real Release batch.
- [ ] “稍后处理” preserves pending batch.
- [ ] Save completion updates global `savedResources` with no manual sync event.
- [ ] Empty batch does not show fake pending count or forced Review CTA.
- [ ] Verify Publish → Review → Save → My Resources → back → Review state preserved.
- [ ] Commit: `feat: complete release to resource library flow`.

---

# Task 11: 跨项目真实复用闭环

**Files**
- Modify `frontend/src/stores/projectStore.ts`
- Modify `frontend/src/screens/K01CreateProject.vue`
- Modify `frontend/src/components/workspace/GameSpecDocument.vue`
- Modify `frontend/src/components/workspace/ResourceReuseRecommendation.vue`
- Modify `frontend/src/components/workspace/ResourceReuseDrawer.vue`

Steps:
- [ ] Project A saving does not reset global resource library on project switch.
- [ ] Project B is created through real K01/Kickoff, not seed.
- [ ] B generation reads global library through matcher.
- [ ] Use resource updates only relationship fields and shows one reuse status bar.
- [ ] Cancel restores only relationship fields.
- [ ] Dismiss persists through leave/reopen and ordinary revision.
- [ ] Verify full Project A → saved resource → Project B → recommendation → use flow.
- [ ] Commit: `feat: complete cross-project resource reuse`.

---

# Task 12: 删除旧的重复真相源与 URL 业务分支

**Files**
- Modify as needed across App/K02/ResourceReview/BuildPreview/VersionHistory/store/demoSeeds.

Checks:

```bash
grep -R "playableVersion" frontend/src -n
grep -R "currentRelease" frontend/src -n
grep -R "releaseCount" frontend/src -n
grep -R "URLSearchParams\|location.search" frontend/src -n
grep -R "setTimeout" frontend/src -n
grep -R "basedOnGameDesign: 2\|basedOnGameSpec: 2\|basedOnPlayable: 2" frontend/src -n
```

Rules:
- [ ] Derived getter/computed names are allowed; persisted duplicate values are not.
- [ ] URL reads only in App/demo bootstrap.
- [ ] Component `setTimeout` only for visual feedback, never generation/build/change/publish/save.
- [ ] ResourceReview has no locally cloned candidate truth.
- [ ] No hard-coded Release base version numbers.
- [ ] Full typecheck/build passes.
- [ ] Commit: `chore: remove legacy lifecycle state paths`.

---

# Task 13: 全链路浏览器验收

## Scenario A — 农场项目沉淀资源

- [ ] No-param startup: Projects empty, My Resources empty.
- [ ] Create farm Idea → Kickoff → Confirm Design.
- [ ] GameSpec review has no recommendation because library empty.
- [ ] Confirm Spec → Build.
- [ ] Leave during Build; return after wait; progress preserved.
- [ ] Playable v1 real record exists.
- [ ] Controlled Change → Playable v2.
- [ ] Version History shows v1/v2.
- [ ] Restore v1 → v3 with `reason='restore'`, `restoredFrom=1`, v1 snapshot.
- [ ] Publish Release v1 with real provenance.
- [ ] Resource Review shows that Release batch.
- [ ] Save `relationship-system`; leave while saving; return => saved.
- [ ] My Resources grows 0→1.

## Scenario B — 咖啡店项目复用

- [ ] Create coffee Idea through real flow.
- [ ] coffeeScenario is selected.
- [ ] Confirm Design → GameSpec.
- [ ] NPC section auto-recommends saved `relationship-system`.
- [ ] Drawer uses “为什么适合当前设计”.
- [ ] Drawer has no “不包含”.
- [ ] Use resource → one reuse status bar only.
- [ ] GameSpec relationship fields adapt with machine defaults.
- [ ] No Lucy/farm content appears.
- [ ] Cancel restores only relationship fields.
- [ ] Other section changes remain.
- [ ] Dismiss persists across navigation + ordinary revision.

## Scenario C — 多项目

- [ ] Two projects visible in Projects.
- [ ] Stage labels correct.
- [ ] updatedAt changes correctly.
- [ ] Project states do not contaminate each other.
- [ ] Global savedResources is shared.

## Scenario D — Demo Seeds

Smoke:

```text
?screen=gamespec
?screen=build
?screen=change
?screen=publish
?screen=resource-reuse
?screen=resources
?screen=my-resources
```

- [ ] Each loads correctly.
- [ ] `resource-reuse` reaches recommendation through matcher.
- [ ] Console has no app-owned warning/error.

## Scenario E — Error Injection

- [ ] specError
- [ ] buildError
- [ ] scopeError
- [ ] publishError
- [ ] kickoffError
- [ ] Retry paths recover.
- [ ] No stuck timers.
- [ ] No cross-job timer cancellation.

---

# Task 14: Prototype Freeze

**Files**
- Create `docs/superpowers/verification/2026-08-12-project-lifecycle-verification.md`
- Update README/demo instructions only if needed.

Steps:
- [ ] Record state ownership model.
- [ ] Record real two-project demo story.
- [ ] Record deliberately deferred scope:
  - backend persistence
  - DB Project/Version/Release
  - semantic/LLM matching
  - real OpenGame runtime
  - real resource code/asset injection
  - team permissions
  - marketplace/team library
- [ ] Final commands:

```bash
cd frontend
npx vue-tsc -b
npx vite build
git status --short
```

- [ ] Final commit: `docs: freeze project lifecycle prototype`.

---

# Final Definition of Done

- [ ] Empty real startup works.
- [ ] Multiple projects persist independently.
- [ ] Leaving Workspace does not destroy business progress.
- [ ] Timers isolated by project + job key.
- [ ] No unmounted component business timer mutates store.
- [ ] `playableVersions[]` is sole Playable truth.
- [ ] `releases[]` is sole Release truth.
- [ ] Restore creates a new version with copied snapshot.
- [ ] BuildPreview reads snapshot, not global farm fixture assumptions.
- [ ] Release owns its own candidate batch.
- [ ] Empty candidate batches work.
- [ ] Candidate saving cannot stick forever.
- [ ] Resource library begins empty and grows only after Human Gate save.
- [ ] Project A resource can be recommended in Project B.
- [ ] Matcher uses structured GameSpec fields.
- [ ] Reuse defaults are machine-readable.
- [ ] dismiss persists through current specVersion.
- [ ] use/cancel only affects intended relationship fields.
- [ ] Coffee Idea is reachable through real Kickoff.
- [ ] Demo URLs seed store instead of driving component business logic.
- [ ] Error demo routes still recover.
- [ ] `npx vue-tsc -b && npx vite build` passes.
- [ ] Two-project browser demo runs without app-owned console errors.

---

# Execution Order

```text
1 Domain model/store skeleton
2 Store lifecycle/timers
3 Playable/Release/Restore
4 Release resource batches
5 Real resource matching/reuse
6 Projects/App shell
7 Demo seeds
8 Coffee real route
9 Preview decoupling
10 Release→Library closure
11 Cross-project reuse closure
12 Legacy cleanup
13 End-to-end verification
14 Prototype Freeze
```

Do not parallelize Tasks 1–7.
Tasks 8–9 may run in parallel only after Task 7 is green.
Tasks 10–14 run on the integrated result.

---

# Codex Execution Prompt

```text
@Superpowers

Execute `docs/superpowers/plans/2026-08-12-project-lifecycle-state-store.md`.

Use superpowers:subagent-driven-development if available; otherwise use superpowers:executing-plans.

Constraints:
- Follow tasks in order.
- Do not redesign the product.
- Do not introduce Pinia, Vue Router, backend APIs, or new runtime dependencies.
- Keep pure UI state local to components.
- Keep business lifecycle mutations behind projectStore actions.
- Preserve existing prototype visual language.
- After every task, run `cd frontend && npx vue-tsc -b && npx vite build`.
- Do not silently skip failing verification.
- Do not broaden scope when encountering unrelated cleanup.
- Commit after each task using the commit message in the plan.
- Before claiming completion, run Task 13 browser acceptance and Task 14 final verification.
```
