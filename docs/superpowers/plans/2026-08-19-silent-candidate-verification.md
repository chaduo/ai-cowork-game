# Silent Candidate Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically verify each real Build Candidate, rebuild and re-verify failed Candidates for at most three repair rounds, then stop at explicit Human Play Review and Promote gates.

**Architecture:** Add a pure frontend policy module that decides the next verification action and builds a bounded repair prompt from persisted evidence. The existing project store owns the asynchronous verify/rebuild loop and reuses the existing idempotent Candidate test, Build, and repair-link APIs. The Workspace renders quiet progress by default and an optional Candidate preview/evidence detail surface; it never automates Human Play Review or Promote.

**Tech Stack:** Vue 3 Composition API, TypeScript 5.7, Node test runner, existing FastAPI Candidate/Build APIs.

## Global Constraints

- A successful Build creates a Candidate, not a Playable.
- Platform Verification runs automatically; Human Play Review and Promote remain explicit user actions.
- A replacement Candidate is linked to its failed parent before replacement verification begins.
- Automatic repair stops after `repair_round == 3` and never changes the current Playable.
- Persisted TestReports and evidence are immutable and reused.
- Do not stream or pretend to stream the backend Chrome screen.
- Preserve unrelated local Game Design provider changes.

## File Structure

- Create `frontend/src/contracts/candidateVerificationFlow.ts`: pure action selection and repair-prompt construction.
- Create `frontend/tests/candidateVerificationFlow.test.mjs`: contract tests for automatic verification and repair policy.
- Modify `frontend/src/stores/projectStore.ts`: asynchronous orchestration using existing API functions.
- Modify `frontend/src/screens/K02ProjectWorkspace.vue`: restore review notes and render quiet automatic verification with optional details.
- Modify `frontend/src/components/workspace/BuildCoworkPanel.vue`: remove automatic Human Gate claims.

---

### Task 1: Verification And Repair Policy

**Files:**
- Create: `frontend/src/contracts/candidateVerificationFlow.ts`
- Create: `frontend/tests/candidateVerificationFlow.test.mjs`

**Interfaces:**
- Consumes: `CandidateTestReportResponse`-compatible report fields `summary`, `diagnostics`, and `evidence`.
- Produces: `nextCandidateVerificationAction(input): 'verify' | 'repair' | 'human_review' | 'manual_retry' | 'wait' | 'stopped'`.
- Produces: `buildCandidateRepairRequest(report): string` bounded to the API request limit of 4,000 characters.

- [ ] **Step 1: Write failing policy tests**

```js
test('automatically verifies an untested candidate', () => {
  assert.equal(nextCandidateVerificationAction({
    testGateStatus: 'untested', hasReport: false, repairRound: 0,
    testRunning: false, repairRunning: false, hasTransportError: false,
  }), 'verify')
})

test('stops automatic work at human review after pass', () => {
  assert.equal(nextCandidateVerificationAction({
    testGateStatus: 'ready', hasReport: true, repairRound: 1,
    testRunning: false, repairRunning: false, hasTransportError: false,
  }), 'human_review')
})

test('repairs a persisted failure below the repair limit', () => {
  assert.equal(nextCandidateVerificationAction({
    testGateStatus: 'failed', hasReport: true, repairRound: 2,
    testRunning: false, repairRunning: false, hasTransportError: false,
  }), 'repair')
})

test('stops after three repair rounds', () => {
  assert.equal(nextCandidateVerificationAction({
    testGateStatus: 'failed', hasReport: true, repairRound: 3,
    testRunning: false, repairRunning: false, hasTransportError: false,
  }), 'stopped')
})

test('requires manual retry after a transport failure without a report', () => {
  assert.equal(nextCandidateVerificationAction({
    testGateStatus: 'untested', hasReport: false, repairRound: 0,
    testRunning: false, repairRunning: false, hasTransportError: true,
  }), 'manual_retry')
})
```

```js
test('builds a bounded repair request from persisted failure evidence', () => {
  const request = buildCandidateRepairRequest({
    repairRound: 1,
    summary: 'Core gameplay acceptance failed',
    diagnostics: [{ code: 'movement_stuck', message: 'Player did not move' }],
    evidence: [{ kind: 'core_input', status: 'failed', observed: 'x remained 0' }],
  })
  assert.match(request, /Repair round 2 of 3/)
  assert.match(request, /Core gameplay acceptance failed/)
  assert.match(request, /core_input: x remained 0/)
  assert.match(request, /movement_stuck: Player did not move/)
  assert.ok(request.length <= 4000)
})
```

- [ ] **Step 2: Run the test and verify RED**

Run: `node --test frontend/tests/candidateVerificationFlow.test.mjs`

Expected: FAIL because `candidateVerificationFlow.ts` does not exist.

- [ ] **Step 3: Implement the minimal pure policy**

```ts
export const MAX_AUTOMATIC_REPAIR_ROUNDS = 3

export function nextCandidateVerificationAction(input: CandidateVerificationState): CandidateVerificationAction {
  if (input.testRunning || input.repairRunning) return 'wait'
  if (input.testGateStatus === 'ready') return 'human_review'
  if (input.hasTransportError && !input.hasReport) return 'manual_retry'
  if (!input.hasReport && (!input.testGateStatus || input.testGateStatus === 'untested')) return 'verify'
  if (input.hasReport && ['failed', 'invalid'].includes(input.testGateStatus ?? '')) {
    return input.repairRound < MAX_AUTOMATIC_REPAIR_ROUNDS ? 'repair' : 'stopped'
  }
  return 'wait'
}
```

```ts
export type CandidateFailureReport = {
  repairRound: number
  summary: string
  diagnostics: Array<Record<string, unknown>>
  evidence: Array<{ kind: string; status: string; observed: string }>
}

function diagnosticLine(item: Record<string, unknown>): string {
  const code = typeof item.code === 'string' ? item.code : 'diagnostic'
  const message = typeof item.message === 'string' ? item.message : JSON.stringify(item)
  return `${code}: ${message}`
}

export function buildCandidateRepairRequest(report: CandidateFailureReport): string {
  const evidence = report.evidence
    .filter((item) => item.status === 'failed' || item.status === 'missing')
    .map((item) => `${item.kind}: ${item.observed}`)
  const lines = [
    `Repair round ${report.repairRound + 1} of ${MAX_AUTOMATIC_REPAIR_ROUNDS}.`,
    'Repair the existing game according to this platform-owned verification report.',
    `Summary: ${report.summary}`,
    ...evidence.map((item) => `Evidence: ${item}`),
    ...report.diagnostics.map((item) => `Diagnostic: ${diagnosticLine(item)}`),
    'Keep the confirmed GameSpec and unaffected behavior unchanged. Produce a complete index.html Candidate.',
  ]
  return lines.join('\n').slice(0, 4000)
}
```

- [ ] **Step 4: Run the policy tests and verify GREEN**

Run: `node --test frontend/tests/candidateVerificationFlow.test.mjs`

Expected: all policy and prompt tests PASS.

- [ ] **Step 5: Commit the policy**

```bash
git add frontend/src/contracts/candidateVerificationFlow.ts frontend/tests/candidateVerificationFlow.test.mjs
git commit -m "feat: define automatic candidate verification policy"
```

### Task 2: Automatic Store Orchestration

**Files:**
- Modify: `frontend/src/stores/projectStore.ts`
- Test: `frontend/tests/candidateVerificationFlow.test.mjs`

**Interfaces:**
- Consumes: `nextCandidateVerificationAction` and `buildCandidateRepairRequest` from Task 1.
- Produces: `ensureRemoteCandidateVerification(projectId: string): Promise<void>`.
- Changes: `testRemoteCandidate(projectId: string): Promise<CandidateResponse | null>`.
- Changes: `rebuildRemoteCandidate(projectId: string, requestText?: string): Promise<CandidateResponse | null>`.

- [ ] **Step 1: Extend failing tests for state carried between attempts**

```js
for (const state of [
  { testRunning: true, repairRunning: false },
  { testRunning: false, repairRunning: true },
]) {
  assert.equal(nextCandidateVerificationAction({
    testGateStatus: 'untested', hasReport: false, repairRound: 0,
    hasTransportError: false, ...state,
  }), 'wait')
}

assert.equal(nextCandidateVerificationAction({
  testGateStatus: 'invalid', hasReport: true, repairRound: 2,
  testRunning: false, repairRunning: false, hasTransportError: false,
}), 'repair')
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `node --test frontend/tests/candidateVerificationFlow.test.mjs`

Expected: FAIL on the newly added cases until the policy supports every store state.

- [ ] **Step 3: Carry Candidate attempt metadata in remote state**

Add these exact fields to `RemoteBuildState`:

```ts
attempt?: number
repairRound?: number
repairRunning?: boolean
```

Import `type CandidateResponse` from `../api/client`. When Candidate test or repair-link APIs return a `CandidateResponse`, assign:

```ts
remote.testGateStatus = response.test_gate_status
remote.testReport = response.report
remote.attempt = response.attempt
remote.repairRound = response.repair_round
```

- [ ] **Step 4: Make existing operations return their durable result**

Change `testRemoteCandidate` to return `response` after updating state and `null` in its catch path. Change `startRemoteBuild` to accept `requestText = '根据已确认的 GameSpec 创建第一个可试玩版本，并生成真实 index.html。'` and pass that value to `createProjectBuild`.

Change `rebuildRemoteCandidate(projectId, requestText)` to set `repairRunning`, call `startRemoteBuild(projectId, requestText)`, link the replacement Candidate, copy the returned attempt metadata into the replacement `remoteBuild`, return the repair-link response, and clear `repairRunning` in `finally`. Existing UI callers may ignore the returned promise value.

- [ ] **Step 5: Add the guarded orchestration loop**

```ts
const candidateVerificationJobs = new Set<string>()

export async function ensureRemoteCandidateVerification(projectId: string): Promise<void> {
  const session = getProject(projectId)
  if (!session?.backendProjectId || !session.remoteBuild?.candidateId || candidateVerificationJobs.has(projectId)) return
  candidateVerificationJobs.add(projectId)
  try {
    while (true) {
      const current = getProject(projectId)?.remoteBuild
      if (!current?.candidateId) return
      const action = nextCandidateVerificationAction({
        testGateStatus: current.testGateStatus,
        hasReport: Boolean(current.testReport),
        repairRound: current.repairRound ?? 0,
        testRunning: Boolean(current.testRunning),
        repairRunning: Boolean(current.repairRunning),
        hasTransportError: Boolean(current.testError),
      })
      if (action === 'verify') {
        if (!await testRemoteCandidate(projectId)) return
        continue
      }
      if (action === 'repair') {
        const report = current.testReport!
        const request = buildCandidateRepairRequest({
          repairRound: current.repairRound ?? 0,
          summary: report.summary,
          diagnostics: report.diagnostics,
          evidence: report.evidence,
        })
        if (!await rebuildRemoteCandidate(projectId, request)) return
        continue
      }
      return
    }
  } finally {
    candidateVerificationJobs.delete(projectId)
  }
}
```

At the end of `applyRemoteBuildState`, after `applyRemoteWorkspaceRoute`, call `void ensureRemoteCandidateVerification(session.id)` only when the route is `candidate`. The project-keyed job guard prevents the nested replacement Build response from starting a second loop. After refresh has loaded Candidate test/review state, call the same function when the restored route is `candidate`. Do not call it for `playable`.

- [ ] **Step 6: Run all frontend contract tests**

Run: `for f in frontend/tests/*.test.mjs; do node "$f" || exit 1; done`

Expected: all contract tests PASS with no duplicate-call policy regression.

- [ ] **Step 7: Commit orchestration**

```bash
git add frontend/src/stores/projectStore.ts frontend/tests/candidateVerificationFlow.test.mjs
git commit -m "feat: automate candidate verification and repair"
```

### Task 3: Quiet Verification And Explicit Human Gate UI

**Files:**
- Modify: `frontend/src/screens/K02ProjectWorkspace.vue`
- Modify: `frontend/src/components/workspace/BuildCoworkPanel.vue`

**Interfaces:**
- Consumes: `ensureRemoteCandidateVerification(projectId)` and `RemoteBuildState` verification fields from Task 2.
- Preserves: existing `reviewRemoteCandidate` and `promoteRemoteCandidate` explicit commands.

- [ ] **Step 1: Reproduce the existing build failure**

Run: `npm run build` from `frontend/`.

Expected: FAIL because `humanReviewNotes` is referenced but not declared.

- [ ] **Step 2: Restore review notes and remove false automatic-gate copy**

Restore:

```ts
const humanReviewNotes = ref('')
```

Remove `autoDeliveryStatus` from `BuildCoworkPanel`. Candidate-ready copy becomes: “平台验证会自动执行；通过后仍需你完成人工试玩确认。”

- [ ] **Step 3: Replace manual verification with quiet progress**

Replace the initial command with these state branches:

```vue
<span v-if="session.remoteBuild?.testRunning"><LoaderCircle class="spin" />Chrome 正在执行平台验证</span>
<span v-else-if="session.remoteBuild?.repairRunning"><LoaderCircle class="spin" />正在生成修复 Candidate</span>
<span v-else-if="session.remoteBuild?.testGateStatus === 'ready'"><Check />平台验证通过</span>
<button v-else-if="(session.remoteBuild?.repairRound ?? 0) >= 3" type="button" @click="rebuildCandidate">重新尝试</button>
```

- [ ] **Step 4: Add optional test details**

Use a native disclosure with this structure:

```vue
<details class="candidate-test-details">
  <summary>查看浏览器测试详情</summary>
  <p v-if="session.remoteBuild?.testRunning">Chrome 正在执行页面启动、核心输入、玩法循环与完成条件检查。</p>
  <iframe v-if="session.remoteBuild?.candidatePreviewUrl" :src="session.remoteBuild.candidatePreviewUrl" title="Candidate 预览"></iframe>
  <ul v-if="session.remoteBuild?.testReport" class="candidate-evidence-list">
    <li v-for="evidence in session.remoteBuild.testReport.evidence" :key="evidence.id" :class="`is-${evidence.status}`">
      <Check v-if="evidence.status === 'passed'" />
      <CircleX v-else />
      <span><strong>{{ evidenceLabels[evidence.kind] ?? evidence.kind }}</strong><small>{{ evidenceObserved(evidence) }}</small></span>
    </li>
  </ul>
</details>
```

Inside it:

- show an honest running state before a report exists;
- show the Candidate iframe when `candidatePreviewUrl` is available;
- show the existing evidence list after a report exists;
- never label the iframe as the backend Chrome session.

Keep Human Play Review controls disabled until `testGateStatus === 'ready'`. Preserve the separate Promote button after an accepted review.

- [ ] **Step 5: Run build and frontend tests**

Run: `npm run build` from `frontend/`.

Expected: `vue-tsc -b` and Vite build PASS.

Run: `for f in frontend/tests/*.test.mjs; do node "$f" || exit 1; done`

Expected: all frontend contract tests PASS.

- [ ] **Step 6: Commit UI changes**

```bash
git add frontend/src/screens/K02ProjectWorkspace.vue frontend/src/components/workspace/BuildCoworkPanel.vue
git commit -m "fix: keep automatic verification behind human gates"
```

### Task 4: Regression Verification

**Files:**
- Verify only; no planned production edits.

**Interfaces:**
- Consumes all outputs from Tasks 1-3.
- Produces fresh verification evidence for handoff.

- [ ] **Step 1: Run focused backend gate tests**

Run from `backend/`:

```bash
./.venv/bin/pytest -q tests/test_c12_candidate_test_gate.py tests/test_c12_candidate_api.py tests/test_c14_api.py
```

Expected: all focused tests PASS.

- [ ] **Step 2: Run the non-browser backend regression suite**

Run from `backend/`:

```bash
./.venv/bin/pytest -q --ignore=tests/test_browser_runner_real_candidate.py
```

Expected: all non-browser backend tests PASS; the existing Starlette/httpx deprecation warning may remain.

- [ ] **Step 3: Run final frontend verification**

Run from `frontend/`:

```bash
for f in tests/*.test.mjs; do node "$f" || exit 1; done
npm run build
```

Expected: all contract tests and production build PASS.

- [ ] **Step 4: Inspect scope and Human Gate invariants**

Run:

```bash
git diff --check
git diff -- frontend/src backend/app docs/superpowers/specs docs/superpowers/plans
```

Confirm that automatic code calls only verification, Build, and repair-link APIs; `recordHumanPlayReview` and `promoteBuildCandidate` remain reachable only from explicit user commands.
