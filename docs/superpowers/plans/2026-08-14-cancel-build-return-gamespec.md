# Cancel Build and Return to GameSpec Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make cancelling the first Build stop all scheduled work and return the Workspace to editable GameSpec Review without creating a Playable.

**Architecture:** Treat cancellation as a Build/Run outcome rather than a persistent Workspace phase. `projectStore.cancelBuild()` owns business-state mutation and timer cleanup; `K02ProjectWorkspace` owns only the active artifact tab. Existing GameSpec Review and Human Confirm UI provide both edit-before-rebuild and unchanged-spec rebuild paths.

**Tech Stack:** Vue 3, TypeScript, Vite, deterministic Prototype store, in-app browser acceptance.

## Global Constraints

- Preserve all current GameSpec content when a Build is cancelled.
- Do not create or update a PlayableVersion on cancellation.
- Do not add Pinia, Vue Router, backend APIs, dependencies, or a new confirmation UI.
- Controlled Change cancellation behavior is out of scope.
- Business lifecycle mutation stays behind `projectStore` actions; artifact-tab selection stays local to `K02ProjectWorkspace`.

---

### Task 1: Return Cancellation to GameSpec Review

**Files:**
- Modify: `frontend/src/stores/projectStore.ts`
- Modify: `frontend/src/screens/K02ProjectWorkspace.vue`
- Modify: `frontend/src/components/workspace/buildTypes.ts`

**Interfaces:**
- Consumes: `clearJob(projectId, key)`, `ProjectSession.phase`, existing `review` phase.
- Produces: `cancelBuild(projectId: string): void` that clears pending jobs and sets `session.phase = 'review'`.

- [x] **Step 1: Record the failing browser acceptance**

Open `http://127.0.0.1:4173/?screen=build`, click `取消构建`, and inspect the DOM.

Expected RED evidence before the fix:

```text
BUILD Cancelled remains selected
BUILD CANCELLED remains visible
GAME SPEC tab is absent
```

- [x] **Step 2: Implement the minimal store transition**

Change `cancelBuild()` to preserve the spec and return the Workspace to review:

```ts
export function cancelBuild(projectId: string): void {
  const session = getProject(projectId)
  if (!session || !cancellableBuildPhases.includes(session.phase as BuildPhase)) return
  clearJob(projectId, 'generation')
  clearJob(projectId, 'build')
  session.phase = 'review'
  session.messages.push({
    id: `build-cancelled-${Date.now()}`,
    role: 'system',
    text: 'Build 已取消。当前 GameSpec 保持不变，可以调整后重新确认。',
  })
  touchProject(session)
}
```

Delete `restartBuild()` and remove `build_cancelled` from `BuildPhase`.

- [x] **Step 3: Switch the artifact tab after cancellation**

Update the component handler:

```ts
function cancelBuildStage() {
  cancelBuild(session.id)
  activeTab.value = 'gamespec'
}
```

Remove the `restartBuild` import, handler, event binding, and `build_cancelled` build-phase entry.

- [x] **Step 4: Run the TypeScript/build check**

Run:

```bash
cd frontend
npx vue-tsc -b
npx vite build
```

Expected: both commands exit `0`.

### Task 2: Remove the Obsolete Cancelled Build UI

**Files:**
- Modify: `frontend/src/components/workspace/BuildWorkspaceView.vue`
- Modify: `frontend/src/components/workspace/BuildCoworkPanel.vue`
- Modify: `frontend/src/components/workspace/LifecycleRail.vue`
- Modify: `frontend/src/components/workspace/buildFixture.ts`
- Modify: `frontend/src/screens/K01CreateProject.vue`
- Modify: `frontend/src/style.css`

**Interfaces:**
- Consumes: Task 1 `cancelBuild()` transition to `review`.
- Produces: Build UI exposes only the running-phase `cancel` event; Projects derives `GameSpec` after cancellation.

- [x] **Step 1: Remove obsolete UI branches**

`BuildWorkspaceView` keeps only:

```ts
const emit = defineEmits<{ retry: []; cancel: [] }>()
```

Delete the restart button, cancelled status, cancelled panel, `Ban`/`RotateCcw` imports used only by that state, and the `restart` event.

- [x] **Step 2: Remove obsolete state mappings**

Delete `build_cancelled` from:

```text
BuildCoworkPanel labels and branches
LifecycleRail build phase mapping
buildFixture activeOrder
K01 projectStage override
```

Delete CSS selectors used only by `build_cancelled`; retain the running Build cancel-button styling.

- [x] **Step 3: Run the TypeScript/build check**

Run:

```bash
cd frontend
npx vue-tsc -b
npx vite build
```

Expected: both commands exit `0`.

### Task 3: Browser Regression Acceptance

**Files:**
- Verify: `frontend/src/stores/projectStore.ts`
- Verify: `frontend/src/screens/K02ProjectWorkspace.vue`
- Verify: `frontend/src/components/workspace/BuildWorkspaceView.vue`

**Interfaces:**
- Consumes: `?screen=build` deterministic fixture and the running Build cancel button.
- Produces: browser evidence for cancellation, timer stability, reconfirmation, and Projects stage.

- [x] **Step 1: Verify cancellation returns to GameSpec**

From `?screen=build`, click `取消构建` and assert:

```text
GAME SPEC tab is present and selected
GameSpec document content is visible
确认规格并开始构建 is visible
BUILD CANCELLED is absent
```

- [x] **Step 2: Verify the cancelled timer cannot advance**

Wait at least 10 seconds and assert that GameSpec Review remains visible and no Playable exists.

- [x] **Step 3: Verify unchanged-spec reconfirmation**

Click `确认规格并开始构建`, confirm through the existing Human Gate, and assert BUILD enters `WORKING BUILD` again.

- [x] **Step 4: Verify Projects stage**

Open `?screen=gamespec`, confirm through the existing Human Gate, cancel the first Build, return to Projects, and assert the project stage is `GameSpec`, not `Building` or `Build 已取消`. The `?screen=build` fixture preloads a Playable for Preview coverage and therefore cannot prove this assertion.

- [x] **Step 5: Run final verification**

Run:

```bash
cd frontend
npx vue-tsc -b
npx vite build
cd ..
git diff --check
git status --short
```

Expected: typecheck/build/diff check exit `0`; status contains only the intended frontend changes plus pre-existing unrelated files.
