# Controlled Change & Rebuild Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the current mock workspace from `Playable v1 · Stable` through one controlled AI change, safe rebuild, validation repair, `Playable v2 · Stable`, and Version History.

**Architecture:** Add a dedicated controlled-change phase model and fixture beside the existing first-build model. Keep orchestration in `K02ProjectWorkspace.vue`, render focused prop-driven components inside the existing shell, and make Preview version-aware without connecting any backend or runtime.

**Tech Stack:** Vue 3.5, TypeScript 5.7, Vite 6, lucide-vue-next, deterministic local timers, existing CSS tokens and farm preview bitmap.

## Global Constraints

- Preserve K01, Template Gallery, Creative Kickoff, GameSpec, First Build, and the workspace shell.
- Mock data and local state only; no OpenGame, LLM, backend, Git, filesystem, Phaser build, or asset generation.
- User-facing copy is Chinese-first and must not expose Candidate, raw Git diff, or tool thoughts.
- Playable v1 remains stable until changed behavior and regression validation both pass.
- The journey ends at Version History; no Restore or second recommendation cycle.
- Recommendations remain optional and only create a Change Request.

---

### Task 1: Controlled Change Domain Model

**Files:**
- Create: `frontend/src/components/workspace/changeTypes.ts`
- Create: `frontend/src/components/workspace/changeFixture.ts`
- Modify: `frontend/src/components/workspace/workspaceTypes.ts`

**Interfaces:**
- Produces: `ChangePhase`, `ChangeSource`, `ChangePlan`, `ChangeProgressStep`, `ChangeValidationCheck`, `controlledChangePlan`, `getChangeStepStatus()`.
- Consumes: no UI component state.

- [ ] **Step 1:** Define the approved phase union from recommendations through version history.
- [ ] **Step 2:** Define one `ChangePlan` shared by suggestion, natural language, and future direct GameSpec edits.
- [ ] **Step 3:** Add the relationship-feedback fixture with Gameplay and Visual changes, affected/reused artifacts, build strategy, seven progress steps, two changed checks, and four regression checks.
- [ ] **Step 4:** Add pure status helpers for completed, active, upcoming, and failed scope-check steps.
- [ ] **Step 5:** Run `npm run build`; expect the existing application to compile before component integration.

---

### Task 2: Recommendation and Cowork Entry Points

**Files:**
- Create: `frontend/src/components/workspace/NextStepRecommendations.vue`
- Create: `frontend/src/components/workspace/ControlledChangeCoworkPanel.vue`

**Interfaces:**
- `ControlledChangeCoworkPanel` consumes `phase: ChangePhase` and `plan: ChangePlan`.
- Emits `select(directionId)`, `submit(text)`, `continuePlaying`, and `showRecommendations`.

- [ ] **Step 1:** Render the first-playable summary and three compact stacked recommendations.
- [ ] **Step 2:** Mark only the NPC relationship direction as `AI 推荐` and keep all cards optional.
- [ ] **Step 3:** Add a free-form composer that emits the same Change Request path as a card.
- [ ] **Step 4:** Implement `先继续试玩` and a weak re-open action without creating a build.
- [ ] **Step 5:** Render phase-specific AI activity for analysis, reuse, scope, validation failure, repair, and v2 completion.
- [ ] **Step 6:** Run `npm run build`; expect Vue templates and emitted event types to pass.

---

### Task 3: Change Analysis and Human Gate

**Files:**
- Create: `frontend/src/components/workspace/ChangeAnalysisPanel.vue`
- Create: `frontend/src/components/workspace/ChangeSafetyStrip.vue`

**Interfaces:**
- Consumes `plan: ChangePlan`, `phase: ChangePhase`.
- Emits `apply` and `cancel` only during `change_review`.

- [ ] **Step 1:** Render AI interpretation as two user-facing change goals and Chinese type tags.
- [ ] **Step 2:** Render modification summaries with current and changed behavior.
- [ ] **Step 3:** Render affected artifacts and directly reused content as separate semantic regions.
- [ ] **Step 4:** Add progressive technical disclosure using product concepts rather than file paths.
- [ ] **Step 5:** Add the build strategy notice and non-modal human confirmation footer.
- [ ] **Step 6:** Add the two-track safety strip showing stable v1 beside the Working Build.
- [ ] **Step 7:** Run `npm run build`; expect no prop or artifact-tab type errors.

---

### Task 4: Change-specific Progress, Scope Safety, and Validation

**Files:**
- Create: `frontend/src/components/workspace/ChangeBuildProgress.vue`
- Create: `frontend/src/components/workspace/ChangeValidationPanel.vue`
- Create: `frontend/src/components/workspace/ControlledChangeWorkspace.vue`

**Interfaces:**
- Consumes `phase: ChangePhase`, `plan: ChangePlan`.
- Emits `retryScope` from the blocking scope-violation state.

- [ ] **Step 1:** Render seven change-specific progress rows rather than first-build milestones.
- [ ] **Step 2:** Make reused content the first visible completed outcome.
- [ ] **Step 3:** Render scope checking and a blocking `scope_violation` state with only `重新生成修改`.
- [ ] **Step 4:** Render 2 changed-behavior and 4 regression checks in separate groups.
- [ ] **Step 5:** Fail the Favor HUD refresh during the first validation pass and show automatic repair.
- [ ] **Step 6:** Render 6/6 PASS only during `validation_complete_change` or later.
- [ ] **Step 7:** Run `npm run build`; expect all change artifact states to compile.

---

### Task 5: Version-aware Preview and History

**Files:**
- Modify: `frontend/src/components/workspace/BuildPreview.vue`
- Create: `frontend/src/components/workspace/VersionHistoryDrawer.vue`

**Interfaces:**
- `BuildPreview` accepts `phase: BuildPhase | ChangePhase` and emits `openHistory` when v2 is stable.
- `VersionHistoryDrawer` consumes `open: boolean` and emits `close`.

- [ ] **Step 1:** Keep Preview on stable v1 during every working phase and show a restrained Working Build notice.
- [ ] **Step 2:** Add the heart Favor bar only when v2 passes validation.
- [ ] **Step 3:** Render `Playable v2 · Stable`, `6 / 6 PASS`, and preserved-v1 copy.
- [ ] **Step 4:** Build the v2/v1 history drawer with consistent Design v2 and GameSpec v2 provenance and no Restore action.
- [ ] **Step 5:** Run `npm run build`; expect Preview and history interfaces to pass.

---

### Task 6: Workspace Orchestration

**Files:**
- Modify: `frontend/src/screens/K02ProjectWorkspace.vue`
- Modify: `frontend/src/components/workspace/LifecycleRail.vue`
- Modify: `frontend/src/App.vue`

**Interfaces:**
- `?screen=change` starts at stable v1 recommendations.
- `?screen=change&scopeError=1` triggers one scope violation before retry succeeds.

- [ ] **Step 1:** Add change artifact tabs while reusing Preview, Assets, and Code.
- [ ] **Step 2:** Transition first-build `playable_ready` to recommendations without changing Preview.
- [ ] **Step 3:** Route suggestion and free-form input through one `requestChange(source, summary)` function.
- [ ] **Step 4:** Run analysis timer, human gate, and deterministic working-build sequence.
- [ ] **Step 5:** Preserve v1 through scope failure and validation repair; update to v2 only at 6/6 PASS.
- [ ] **Step 6:** Open Version History only from the v2 state and stop the flow there.
- [ ] **Step 7:** Run `npm run build`; expect full production compilation to pass.

---

### Task 7: Visual Styling and Browser Acceptance

**Files:**
- Modify: `frontend/src/style.css`
- Create: `frontend/screenshots/k04-recommendations-1280x720.png`
- Create: `frontend/screenshots/k04-change-analysis-1280x720.png`
- Create: `frontend/screenshots/k04-working-build-1280x720.png`
- Create: `frontend/screenshots/k04-validation-fix-1280x720.png`
- Create: `frontend/screenshots/k04-playable-v2-history-1280x720.png`
- Create: `frontend/screenshots/k04-scope-violation-1280x720.png`

**Interfaces:**
- Consumes the running Vite app and deterministic routes.
- Produces screenshot evidence and semantic browser assertions.

- [ ] **Step 1:** Add scoped styles using existing tokens, normal body sizes, square geometry, and the two-track safety strip.
- [ ] **Step 2:** Verify recommendation, free-form, and continue-playing entry paths in Chromium.
- [ ] **Step 3:** Verify affected/reuse/human-gate content before application.
- [ ] **Step 4:** Verify v1 remains stable during every working phase and scope violation.
- [ ] **Step 5:** Verify 1 failed changed check, automatic repair, 6/6 PASS, v2 promotion, and v1/v2 history.
- [ ] **Step 6:** Capture screenshots and inspect hierarchy, overlap, truncation, and state-color meaning.
- [ ] **Step 7:** Run final `npm run build` and confirm zero blocking page/console errors.

## Plan Self-review

- Every approved normal and failure state has one owner and one browser assertion.
- First Build and Change Build use separate progress models.
- Recommendation, free-form, and future GameSpec edit sources share one ChangePlan.
- Stable version mutation is impossible before validation completion.
- No prohibited Restore, second cycle, Candidate UI, Monaco, or real integration is introduced.
