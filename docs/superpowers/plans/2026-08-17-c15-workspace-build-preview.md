# C15 Workspace Build Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将真实 Build、Candidate、Human Review 和 Playable 状态接入 K02 Workspace，并通过安全 endpoint 展示已 Promote 的真实 `index.html`。

**Architecture:** 保留现有 Vue Workspace 和 `projectStore` 作为唯一前端业务状态入口；扩展 C14 Playable API 和 C13 Workspace path policy。前端只持有 metadata/Preview URL，不复制 artifact 到 frontend。

**Tech Stack:** FastAPI, SQLAlchemy, existing C13 `WorkspaceManager`, Vue 3, TypeScript, lucide icons, pytest, `vue-tsc`, Vite。

## Global Constraints

- 不引入 Pinia、Vue Router、workflow engine、queue、worker 或新的 runtime dependency。
- 不自动 Promote；Human Play Review 和 Promote 必须由用户明确触发。
- 失败、取消、超时、invalid output 和测试失败不得改变 current Playable。
- Preview 只能读取已 Promote、同一 Project、已验证的 `index.html`。
- 继续复用现有 K02 Workspace、Build 组件和 C13 path policy，不重做全局导航。
- 每个任务完成后运行：`cd frontend && npx vue-tsc -b && npx vite build`，后端任务同时运行对应 pytest。

---

### Task 1: Add the safe Playable Preview endpoint

**Files:**
- Modify: `backend/app/api/playables.py`
- Test: `backend/tests/test_c15_preview_api.py`

**Interfaces:**
- Consumes: `project_id`, `version_id`, `PlayableVersion`, `BuildCandidate`, `Build`, `Run.workspace_path`, `WorkspaceManager.validate_member`。
- Produces: `GET /api/v1/projects/{project_id}/playable-versions/{version_id}/preview` returning the validated `index.html` with `text/html`。

- [ ] **Step 1: Write the failing API tests**

Create a promoted Playable whose Run workspace contains `index.html` with `window.__GAME_TEST__`. Assert the endpoint returns 200 and `text/html`. Add cases for missing file, another project's version, and `artifact_path=../outside.html`; each must return a structured non-200 response without exposing an absolute host path.

- [ ] **Step 2: Run the focused tests and confirm RED**

```bash
backend/.venv/bin/pytest backend/tests/test_c15_preview_api.py -q
```

Expected: the route is not found or the safe artifact assertions fail.

- [ ] **Step 3: Implement the minimal endpoint**

Resolve version ownership, source Candidate → Build → Run, require a promoted Candidate and `index.html`, validate the workspace-relative path with `WorkspaceManager.validate_member`, verify the resolved file is regular and inside the workspace, then return `FileResponse(media_type="text/html")`. Map unsafe/missing records to existing `ApiError` envelopes without returning server paths.

- [ ] **Step 4: Run focused regression**

```bash
backend/.venv/bin/pytest backend/tests/test_c15_preview_api.py backend/tests/test_c14_api.py -q
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/playables.py backend/tests/test_c15_preview_api.py
git commit -m "feat: serve safe playable preview artifact"
```

### Task 2: Extend frontend API contracts and remote session state

**Files:**
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/stores/projectStore.ts`
- Test: `frontend/src/stores/projectStore.c15.test.ts` when an existing frontend test runner is available; otherwise verify with typecheck/build and Task 5 browser acceptance.

**Interfaces:**
- Produces these client functions:

```ts
recordHumanPlayReview(candidateId: string, input: { decision: 'accepted' | 'rejected'; notes?: string }): Promise<HumanPlayReview>
promoteBuildCandidate(candidateId: string, gitCommit: string): Promise<PlayableVersionResponse>
listPlayableVersions(projectId: string): Promise<PlayableVersionResponse[]>
playablePreviewUrl(projectId: string, versionId: string): string
```

- Produces these store actions:

```ts
reviewRemoteCandidate(projectId: string, decision: 'accepted' | 'rejected', notes?: string): Promise<void>
promoteRemoteCandidate(projectId: string): Promise<void>
refreshRemotePlayable(projectId: string): Promise<void>
```

- [ ] **Step 1: Define failing state assertions**

Assert that a failed review/promote leaves `remoteBuild` and the current Playable unchanged, while a successful Promote sets `session.phase` to `playable_ready` and records version id and Preview URL.

- [ ] **Step 2: Run typecheck to confirm RED**

```bash
cd frontend && npx vue-tsc -b
```

- [ ] **Step 3: Add API types/functions and store transitions**

Use the existing `request` and `ApiClientError` wrapper. Do not add a second fetch client. `promoteRemoteCandidate` must never append a local fixture Playable; it only uses the API response.

- [ ] **Step 4: Verify and commit**

```bash
cd frontend && npx vue-tsc -b && npx vite build
git add frontend/src/api/client.ts frontend/src/stores/projectStore.ts
git commit -m "feat: connect workspace human gate state"
```

### Task 3: Restore real state after refresh

**Files:**
- Modify: `backend/app/api/projects.py` if the summary lacks latest review metadata。
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/screens/K02ProjectWorkspace.vue`
- Modify: `frontend/src/stores/projectStore.ts`
- Test: `backend/tests/test_c15_project_state.py`

- [ ] **Step 1: Write failing persistence tests**

Cover: running Build restores as running without a second POST; terminal failed Build restores as `build_error`; a promoted Playable restores `playable_ready` and Preview URL; a passed Candidate with no Human Review restores Candidate Ready rather than Playable.

- [ ] **Step 2: Run tests and confirm RED**

```bash
backend/.venv/bin/pytest backend/tests/test_c15_project_state.py -q
```

- [ ] **Step 3: Implement deterministic hydration/start guard**

Hydrate latest Build, Candidate TestReport, Human Review and current Playable before starting a new Build. Only start when confirmed GameSpec exists and no recoverable Build or Playable exists. Never clear a terminal `remoteBuild` on mount.

- [ ] **Step 4: Verify and commit**

```bash
backend/.venv/bin/pytest backend/tests/test_c15_project_state.py backend/tests/test_c11_build_api.py -q
cd frontend && npx vue-tsc -b && npx vite build
git add backend/app/api/projects.py backend/tests/test_c15_project_state.py frontend/src/App.vue frontend/src/screens/K02ProjectWorkspace.vue frontend/src/stores/projectStore.ts
git commit -m "fix: restore workspace build state after refresh"
```

### Task 4: Add explicit Human Gate and real Preview UI

**Files:**
- Modify: `frontend/src/screens/K02ProjectWorkspace.vue`
- Modify: `frontend/src/components/workspace/BuildPreview.vue`
- Modify: `frontend/src/components/workspace/BuildCoworkPanel.vue`
- Modify: `frontend/src/components/workspace/buildTypes.ts`
- Modify: `frontend/src/stores/projectStore.ts`

- [ ] **Step 1: Add failing browser assertions**

Assert Candidate Ready shows platform verification first; a passed report shows Human Play Review; accepted review shows Promote; promoted state renders an iframe URL containing `/playable-versions/{version_id}/preview`; failed/cancelled Build shows retry and no real iframe.

- [ ] **Step 2: Run assertions and confirm RED**

Run the configured browser harness, or `cd frontend && npx vue-tsc -b && npx vite build` when no frontend test runner is configured. Current static Preview should fail the real iframe assertion.

- [ ] **Step 3: Implement UI transitions**

Add a compact review section to the existing Candidate panel. Keep notes local, disable duplicate submissions, show API errors, and never auto-promote. Pass `previewUrl` and `isRealPreview` to `BuildPreview`; render an accessible stable-aspect-ratio iframe only when a promoted URL exists, otherwise retain the existing empty/working state.

- [ ] **Step 4: Preserve cancel/retry behavior**

Keep cancel for active builds, retry with a fresh backend build id, preserve the previous Playable on failure, and prevent retry while a Build is active.

- [ ] **Step 5: Verify and commit**

```bash
cd frontend && npx vue-tsc -b && npx vite build
git add frontend/src/screens/K02ProjectWorkspace.vue frontend/src/components/workspace/BuildPreview.vue frontend/src/components/workspace/BuildCoworkPanel.vue frontend/src/components/workspace/buildTypes.ts frontend/src/stores/projectStore.ts
git commit -m "feat: add workspace human review and playable preview"
```

### Task 5: End-to-end C15 verification

**Files:**
- Test: `backend/tests/test_c15_e2e_contract.py`
- Modify: `docs/development/C10_C12_REAL_RUNTIME.md`

- [ ] **Step 1: Add deterministic contract coverage**

Assert successful promotion → Preview 200; failed test → Promote 409; rejected review → current Playable unchanged; unsafe Preview path → structured 4xx.

- [ ] **Step 2: Run deterministic and project verification**

```bash
backend/.venv/bin/pytest backend/tests/test_c15_preview_api.py backend/tests/test_c15_project_state.py backend/tests/test_c15_e2e_contract.py -q
backend/.venv/bin/pytest backend/tests -q
cd frontend && npx vue-tsc -b && npx vite build
```

- [ ] **Step 3: Run real acceptance**

With `cowork-real` and Chrome configured, verify one disposable Project through `confirm GameSpec → one Build → succeeded + candidate_id → platform PASSED/ready → accepted Human Review → Promote → iframe Preview → refresh with same version_id and URL`.

- [ ] **Step 4: Commit evidence**

```bash
git add docs/development/C10_C12_REAL_RUNTIME.md backend/tests/test_c15_e2e_contract.py
git commit -m "test: verify c15 real workspace preview flow"
```

## Self-Review Checklist

- Each C15 requirement maps to Tasks 1–5.
- No task introduces a new router, store library, worker or provider.
- Human Review and Promote remain explicit and separate.
- Preview never trusts a raw path and never serves non-promoted Candidates.
- Refresh/retry rules preserve current Playable.
- Every implementation task has a failing-test or browser-assertion step before production changes.
- Real provider verification remains opt-in; deterministic fixture tests cover CI.
