# Build Workspace Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing K02 workspace from confirmed GameSpec through deterministic AI build, validation, automatic repair, and `Playable v1 · Stable`.

**Architecture:** Keep build state in `K02ProjectWorkspace.vue`, model milestones and transitions in focused workspace modules, and render Build/Preview/Assets/Code as prop-driven components. Reuse the existing workspace shell, lifecycle rail, Cowork panel, fixture design, and static game preview asset.

**Tech Stack:** Vue 3.5, TypeScript 5.7, Vite 6, lucide-vue-next, deterministic browser timers, existing CSS token system.

## Global Constraints

- Mock data and local state only; no real LLM, OpenGame, Claude SDK, Phaser build, or backend.
- Preserve K01, Creative Kickoff, and GameSpec review.
- End at `Playable v1 · Stable`; do not add iteration or version history.
- Keep Working Build and Playable visually and semantically distinct.
- Do not expose Candidate terminology, chain-of-thought, terminal logs, or percent progress.
- Assets and Code are read-only in this stage.
- A recoverable Presentation failure must preserve completed milestones.

---

### Task 1: Build State Model and Fixtures

**Files:**
- Create: `frontend/src/components/workspace/buildTypes.ts`
- Create: `frontend/src/components/workspace/buildFixture.ts`
- Modify: `frontend/src/components/workspace/workspaceTypes.ts`

**Interfaces:**
- Produces: `BuildPhase`, `BuildMilestone`, `BuildEvent`, `ValidationCheck`, `buildMilestones`, `validationChecks`, `getCompletedMilestoneIds(phase)`.
- Consumes: the existing `WorkspacePhase` and GameSpec vocabulary.

- [ ] **Step 1: Define the phase union and domain records**

```ts
export type BuildPhase =
  | 'build_starting' | 'building_foundation' | 'building_core'
  | 'building_interaction' | 'building_presentation'
  | 'building_progression' | 'validating' | 'auto_fixing'
  | 'playable_ready' | 'build_error'

export type MilestoneStatus = 'completed' | 'active' | 'upcoming' | 'failed'
```

- [ ] **Step 2: Add six deterministic milestone fixtures**

Each fixture includes `id`, `number`, `title`, `summary`, `features`,
`gameSpecSource`, `executionDetails`, and the phase in which it completes.

- [ ] **Step 3: Add nine validation checks and trace sources**

The two initially failing checks are inheritance triggering and the final
completion state. Auto-fix changes both to passed without changing earlier work.

- [ ] **Step 4: Run the type/build baseline**

Run: `npm run build`
Expected: existing application compiles before UI integration.

---

### Task 2: Build Ledger and Validation Views

**Files:**
- Create: `frontend/src/components/workspace/BuildMilestoneList.vue`
- Create: `frontend/src/components/workspace/BuildMilestoneDetail.vue`
- Create: `frontend/src/components/workspace/ValidationPanel.vue`
- Create: `frontend/src/components/workspace/BuildWorkspaceView.vue`

**Interfaces:**
- Consumes: `phase: BuildPhase`, `milestones: BuildMilestone[]`, `validationChecks: ValidationCheck[]`.
- Produces: a read-only Build artifact with milestone, detail, validation, and retry events.

- [ ] **Step 1: Render the ordered milestone ledger**

Use completed, active, upcoming, and failed states with a single vertical trace
line. The active milestone is labelled `正在制作`; no percentages are shown.

- [ ] **Step 2: Render milestone detail with two disclosure levels**

The default view lists observable features. `功能详情` and `查看执行详情`
disclosures progressively reveal capability and mock file-operation detail.

- [ ] **Step 3: Render Validation 7/9, auto-fix, and 9/9**

Validation rows include their originating GameSpec section. Automatic repair is
shown inline and has no manual Retry action.

- [ ] **Step 4: Render the Presentation error**

Show the failed Lucy asset, preserved completed milestones, and emit `retry` from
the `重新尝试此阶段` button.

- [ ] **Step 5: Run the production build**

Run: `npm run build`
Expected: Vue type checking and Vite production build pass.

---

### Task 3: Preview, Assets, Code, and Build Cowork Activity

**Files:**
- Create: `frontend/src/components/workspace/BuildPreview.vue`
- Create: `frontend/src/components/workspace/AssetGalleryReadOnly.vue`
- Create: `frontend/src/components/workspace/CodeReadOnlyState.vue`
- Create: `frontend/src/components/workspace/BuildCoworkPanel.vue`
- Modify: `frontend/src/style.css`

**Interfaces:**
- `BuildPreview` consumes `phase` and renders unavailable, Working Build, or Playable.
- `BuildCoworkPanel` consumes `phase` and ordered `BuildEvent[]`.
- Assets and Code require no mutable input.

- [ ] **Step 1: Build the three-state Preview**

Reuse `/game-preview.png`. Before Core it is unavailable; after Core it is
`Working Build`; after validation it is `Playable v1 · Stable` with `9 / 9`.

- [ ] **Step 2: Build read-only Assets and Code states**

Assets are grouped by product concepts. Code shows the bounded file outline and
explains that source editing begins after the first playable.

- [ ] **Step 3: Build milestone-level Cowork activity**

Show only outcomes and current intent by default. Keep the composer disabled
with `首个版本完成后可以继续修改`.

- [ ] **Step 4: Add scoped visual styles**

Reuse existing tokens and geometry. Add one ledger trace, restrained state
transitions, visible keyboard focus, and reduced-motion support. Avoid new global
token values unless the current tokens cannot express a required state.

- [ ] **Step 5: Run the production build**

Run: `npm run build`
Expected: no CSS or template integration errors.

---

### Task 4: Workspace Integration and Deterministic Flow

**Files:**
- Modify: `frontend/src/screens/K02ProjectWorkspace.vue`
- Modify: `frontend/src/components/workspace/LifecycleRail.vue`
- Modify: `frontend/src/App.vue`

**Interfaces:**
- `confirmGameSpec()` starts the timed build sequence.
- Query `?screen=build` starts directly at Build Starting for review.
- Query `?screen=build&buildError=1` triggers the one-time Presentation failure.

- [ ] **Step 1: Extend workspace phase ownership**

Replace the current Build Starting end state with deterministic phase timers and
append one meaningful Cowork event per transition.

- [ ] **Step 2: Switch tabs and lifecycle states correctly**

The Build tab becomes active after confirmation. Preview becomes available after
Core Gameplay. `playable_ready` marks Build completed and Playable active, then
selects Preview automatically.

- [ ] **Step 3: Implement local error retry**

The first Presentation attempt fails only when `buildError=1`; retry resumes
Presentation and continues the normal sequence.

- [ ] **Step 4: Add direct deterministic review routes**

`?screen=build` uses the confirmed farm fixture. Existing `gamespec` and
`build-play` routes remain operational.

- [ ] **Step 5: Run complete build verification**

Run: `npm run build`
Expected: `vue-tsc -b` and `vite build` pass.

---

### Task 5: Browser Acceptance and Visual Critique

**Files:**
- Create: `frontend/screenshots/k03-build-progress-1280x720.png`
- Create: `frontend/screenshots/k03-validation-autofix-1280x720.png`
- Create: `frontend/screenshots/k03-playable-ready-1280x720.png`
- Create: `frontend/screenshots/k03-build-error-1280x720.png`

**Interfaces:**
- Consumes the running Vite development server.
- Produces visual evidence and semantic acceptance results.

- [ ] **Step 1: Verify the normal flow in Chromium**

Open `?screen=build`, confirm all six milestones advance, Working Build appears,
Validation shows 7/9 then 9/9, Preview auto-opens, and Playable is active.

- [ ] **Step 2: Verify the failure fixture**

Open `?screen=build&buildError=1`, assert Foundation and Core remain complete,
retry Presentation, and reach Playable Ready.

- [ ] **Step 3: Verify artifact tabs**

Check Assets and Code are read-only and Preview labels Working Build separately
from Playable.

- [ ] **Step 4: Capture and critique screenshots**

Inspect hierarchy, truncation, overlap, scroll behavior, and state-color meaning.
Fix any P0/P1 visual problem and repeat the relevant screenshot.

- [ ] **Step 5: Check browser errors and rebuild**

Expected: zero blocking page/console errors and a passing `npm run build`.

## Plan Self-review

- Every approved state and artifact tab is covered by one task.
- The normal and recoverable-error paths have explicit browser acceptance.
- Component props use the same `BuildPhase` and fixture types throughout.
- No Candidate, iteration, real agent, real build, or editable asset/code scope is introduced.
- No `TBD`, `TODO`, or ambiguous implementation placeholder remains.
