import { reactive } from 'vue'
import type { ConfirmedGameDesign } from '../components/kickoff/kickoffTypes'
import type { ResourceBatchItem, ResourceCandidate } from '../components/resources/resourceTypes'
import type { BuildPhase } from '../components/workspace/buildTypes'
import { createChangePlan } from '../components/workspace/changeFixture'
import type { ChangePhase, ChangePlan, ChangeSource } from '../components/workspace/changeTypes'
import { createGameSpecFixture } from '../components/workspace/gameSpecFixture'
import { createResourceCandidates as createResourceCandidatesFixture } from '../components/resources/resourceFixtures'
import { matchResourcesToSpec } from './resourceMatching'
import type { ReleaseDraft, ReleasePhase, ReleaseRecord } from '../components/workspace/releaseTypes'
import type { CreatorGameSpec } from '../contracts/creatorGameSpec'
import {
  ApiClientError,
  cancelProjectBuild,
  candidatePreviewUrl,
  createProjectBuild,
  getBuildCandidateTestReport,
  getHumanPlayReview,
  getProjectBuild,
  linkBuildCandidateRepair,
  listPlayableVersions,
  playablePreviewUrl,
  promoteBuildCandidate,
  recordHumanPlayReview,
  testBuildCandidate,
  type BuildResponse,
  type CandidateTestReportResponse,
  type HumanPlayReviewResponse,
  type PlayableVersionResponse,
} from '../api/client'
import type {
  CoworkMessage,
  GameSpecModel,
  PlayableVersionRecord,
  RelationshipDraft,
  SpecContext,
  WorkspacePhase,
} from '../components/workspace/workspaceTypes'

export type ProjectSession = {
  id: string
  backendProjectId: string | null
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
  relationshipSnapshot: Readonly<RelationshipDraft> | null
  resourceBridgeAcknowledged: boolean
  resourceBatches: Record<string, ResourceBatchItem[]>
  designStatus: 'draft' | 'submitted' | 'confirmed'
  gamespecStatus: 'missing' | 'draft' | 'confirmed' | 'superseded'
  canonicalGameSpec: CreatorGameSpec | null
  gamespecRevisionId: string | null
  gamespecGitCommit: string | null
  remoteBuild: RemoteBuildState | null
}

export type RemoteBuildState = {
  buildId: string
  runId: string
  status: string
  candidateId: string | null
  artifactPath: string | null
  errorCode: string | null
  errorMessage: string | null
  testGateStatus?: string
  testReport?: CandidateTestReportResponse | null
  candidatePreviewUrl?: string | null
  testRunning?: boolean
  testError?: string | null
  humanReview?: HumanPlayReviewResponse | null
  reviewRunning?: boolean
  reviewError?: string | null
  playableVersion?: PlayableVersionResponse | null
  previewUrl?: string | null
  promoteRunning?: boolean
  promoteError?: string | null
  buildContextHash?: string | null
}

export type ProjectStore = {
  projects: ProjectSession[]
  activeProjectId: string | null
  savedResources: ResourceCandidate[]
}

export const projectStore = reactive<ProjectStore>({
  projects: [],
  activeProjectId: null,
  savedResources: [],
})

let projectCounter = 0
const PROJECT_STORE_STORAGE_KEY = 'ai-cowork-game.project-store.v1'

type PersistedProjectStore = {
  version: 1
  projects: ProjectSession[]
}

function canUseProjectStorage(): boolean {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

function persistProjectStore(): void {
  if (!canUseProjectStorage()) return
  try {
    const payload: PersistedProjectStore = { version: 1, projects: projectStore.projects }
    window.localStorage.setItem(PROJECT_STORE_STORAGE_KEY, JSON.stringify(payload))
  } catch {
    // Storage is an enhancement for the prototype; unavailable storage must
    // not prevent the in-memory workflow from continuing.
  }
}

export function resetProjectStore(): void {
  projectStore.projects.splice(0)
  projectStore.activeProjectId = null
  projectStore.savedResources.splice(0)
  if (canUseProjectStorage()) {
    try {
      window.localStorage.removeItem(PROJECT_STORE_STORAGE_KEY)
    } catch {
      // Ignore storage cleanup failures in demo mode.
    }
  }
}

export function getProject(id: string): ProjectSession | undefined {
  return projectStore.projects.find((project) => project.id === id)
}

export function getActiveProject(): ProjectSession | null {
  if (!projectStore.activeProjectId) return null
  return getProject(projectStore.activeProjectId) ?? null
}

export function getCurrentPlayable(session: ProjectSession): PlayableVersionRecord | null {
  return session.playableVersions[session.playableVersions.length - 1] ?? null
}

export function getCurrentRelease(session: ProjectSession): ReleaseRecord | null {
  return session.releases[session.releases.length - 1] ?? null
}

export function getPendingResourceCount(session: ProjectSession): number {
  const release = getCurrentRelease(session)
  if (!release) return 0
  const batch = session.resourceBatches[release.id] ?? []
  return batch.filter((item) => item.state === 'pending' || item.state === 'saving').length
}

export function extractCandidatesForRelease(projectId: string, releaseId: string): ResourceBatchItem[] {
  return getProject(projectId)?.resourceBatches[releaseId] ?? []
}

function findBatchItem(projectId: string, releaseId: string, candidateId: string): ResourceBatchItem | null {
  return extractCandidatesForRelease(projectId, releaseId).find((item) => item.candidate.id === candidateId) ?? null
}

function cloneResource(resource: ResourceCandidate): ResourceCandidate {
  return {
    ...resource,
    configurableFields: resource.configurableFields.map((field) => ({ ...field })),
    reusableFor: [...resource.reusableFor],
    removedProjectContent: [...resource.removedProjectContent],
    included: [...resource.included],
    excluded: [...resource.excluded],
    matchSignals: resource.matchSignals && { ...resource.matchSignals, signals: [...resource.matchSignals.signals] },
    reuseDefaults: resource.reuseDefaults && { ...resource.reuseDefaults, thresholds: [...resource.reuseDefaults.thresholds] },
  }
}

export function createResourceCandidates(session: ProjectSession, release: ReleaseRecord): ResourceCandidate[] {
  const savedIds = new Set(projectStore.savedResources.map((resource) => resource.id))
  const ignoredIds = new Set(
    Object.entries(session.resourceBatches)
      .filter(([releaseId]) => releaseId !== release.id)
      .flatMap(([, batch]) => batch.filter((item) => item.state === 'ignored').map((item) => item.candidate.id)),
  )
  return createResourceCandidatesFixture(session, release).filter((candidate) => !savedIds.has(candidate.id) && !ignoredIds.has(candidate.id))
}

export function saveCandidate(projectId: string, releaseId: string, candidateId: string): void {
  const session = getProject(projectId)
  const item = findBatchItem(projectId, releaseId, candidateId)
  if (!session || !item || item.state !== 'pending') return
  item.state = 'saving'
  item.candidate.status = 'saving'
  touchProject(session)
  scheduleJob(projectId, `resource-save:${releaseId}:${candidateId}`, () => {
    const completed = findBatchItem(projectId, releaseId, candidateId)
    if (!completed || completed.state !== 'saving') return
    completed.state = 'saved'
    completed.candidate.status = 'saved'
    const savedIndex = projectStore.savedResources.findIndex((resource) => resource.id === candidateId)
    const saved = cloneResource(completed.candidate)
    if (savedIndex === -1) projectStore.savedResources.push(saved)
    else projectStore.savedResources[savedIndex] = saved
    refreshAllResourceMatches()
    touchProject(session)
  }, 420)
}

export function ignoreCandidate(projectId: string, releaseId: string, candidateId: string): void {
  const session = getProject(projectId)
  const item = findBatchItem(projectId, releaseId, candidateId)
  if (!session || !item || item.state !== 'pending') return
  item.state = 'ignored'
  item.candidate.status = 'ignored'
  touchProject(session)
}

export function undoCandidate(projectId: string, releaseId: string, candidateId: string): void {
  const session = getProject(projectId)
  const item = findBatchItem(projectId, releaseId, candidateId)
  if (!session || !item || (item.state !== 'saved' && item.state !== 'ignored')) return
  if (item.state === 'saved') {
    const savedIndex = projectStore.savedResources.findIndex((resource) => resource.id === candidateId)
    if (savedIndex !== -1) projectStore.savedResources.splice(savedIndex, 1)
    refreshAllResourceMatches()
  }
  item.state = 'pending'
  item.candidate.status = 'pending'
  touchProject(session)
}

export function updateSavedResourceMetadata(candidateId: string, patch: Pick<ResourceCandidate, 'name' | 'summary'>): void {
  const saved = projectStore.savedResources.find((resource) => resource.id === candidateId)
  if (!saved) return
  Object.assign(saved, patch, { cardSummary: patch.summary })
  for (const session of projectStore.projects) {
    for (const batch of Object.values(session.resourceBatches)) {
      const item = batch.find((entry) => entry.candidate.id === candidateId && entry.state === 'saved')
      if (item) Object.assign(item.candidate, patch, { cardSummary: patch.summary })
    }
  }
}

export function refreshResourceMatches(projectId: string): void {
  const session = getProject(projectId)
  if (!session) return

  if (session.reuseSpecVersion !== session.specVersion) {
    session.reuseDecisions = {}
    session.relationshipSnapshot = null
    session.reuseSpecVersion = session.specVersion
  }

  session.matchedResources = Object.fromEntries(
    matchResourcesToSpec(session.spec, projectStore.savedResources).map((match) => [match.resourceId, match.section]),
  )
  touchProject(session)
}

function refreshAllResourceMatches(): void {
  projectStore.projects.forEach((project) => refreshResourceMatches(project.id))
}

export function dismissResourceRecommendation(projectId: string, resourceId: string): void {
  const session = getProject(projectId)
  if (!session || session.reuseSpecVersion !== session.specVersion || !session.matchedResources[resourceId]) return
  session.reuseDecisions[resourceId] = 'dismissed'
  touchProject(session)
}

function relationshipDraft(session: ProjectSession): RelationshipDraft {
  const { relationshipGrowth, favorRules, relationshipEvents, requestRewards } = session.spec.characters
  return { relationshipGrowth, favorRules, relationshipEvents, requestRewards }
}

export function useRelationshipResource(projectId: string, resourceId: string): void {
  const session = getProject(projectId)
  const resource = projectStore.savedResources.find((item) => item.id === resourceId)
  if (!session || !resource || session.reuseSpecVersion !== session.specVersion || session.matchedResources[resourceId] !== 'characters' || !resource.reuseDefaults) return

  if (session.relationshipSnapshot === null) session.relationshipSnapshot = Object.freeze(relationshipDraft(session))
  const defaults = resource.reuseDefaults
  const thresholds = defaults.thresholds.join(' / ')
  Object.assign(session.spec.characters, {
    relationshipGrowth: `通过 NPC 委托与日常互动积累好感，并逐步推进关系。`,
    favorRules: `好感范围 ${defaults.favorMin}–${defaults.favorMax}；关系阈值为 ${thresholds}。`,
    relationshipEvents: `达到 ${thresholds} 好感阈值后触发对应的关系事件。`,
    requestRewards: `完成普通委托：好感 +${defaults.requestReward}；完成重要事件：好感 +${defaults.importantEventReward}。`,
  })
  if (!session.spec.updatedSections.includes('characters')) session.spec.updatedSections.push('characters')
  session.reuseDecisions[resourceId] = 'used'
  touchProject(session)
}

export function cancelRelationshipResource(projectId: string, resourceId: string): void {
  const session = getProject(projectId)
  if (!session || session.reuseDecisions[resourceId] !== 'used' || !session.relationshipSnapshot) return
  Object.assign(session.spec.characters, session.relationshipSnapshot)
  delete session.reuseDecisions[resourceId]
  touchProject(session)
}

export function createPlayableSnapshot(session: ProjectSession): PlayableVersionRecord['snapshot'] {
  const characters = session.spec.characters
  const npcNames = characters.npcName.split(/\s*(?:与|、|,|，|&|and)\s*/).filter(Boolean)
  const previewVariant = session.design.scenarioId === 'farm' ? 'farm' : session.design.scenarioId === 'coffee-shop' ? 'coffee' : 'generic'
  return {
    projectTitle: session.spec.title,
    npcNames,
    capabilities: [...session.spec.gameplay.actions, ...session.spec.scope.included].slice(0, 8),
    previewVariant,
    relationshipSummary: characters.relationshipGrowth,
  }
}

export function appendPlayableVersion(projectId: string, input: { name?: string; summary?: string; reason: PlayableVersionRecord['reason']; restoredFrom?: number }): PlayableVersionRecord | null {
  const session = getProject(projectId)
  if (!session) return null
  const version = session.playableVersions.length + 1
  const record: PlayableVersionRecord = {
    version,
    name: input.name ?? `${session.spec.title} · Playable v${version}`,
    summary: input.summary ?? session.spec.buildTarget.goal,
    reason: input.reason,
    restoredFrom: input.restoredFrom,
    basedOnDesign: session.designVersion,
    basedOnSpec: session.specVersion,
    createdAt: Date.now(),
    snapshot: createPlayableSnapshot(session),
  }
  session.playableVersions.push(record)
  touchProject(session)
  return record
}

export function restorePlayable(projectId: string, targetVersion: number): PlayableVersionRecord | null {
  const session = getProject(projectId)
  const target = session?.playableVersions.find((version) => version.version === targetVersion)
  if (!session || !target) return null
  session.spec.title = target.snapshot.projectTitle
  session.spec.characters.npcName = target.snapshot.npcNames.join(' 与 ')
  session.spec.characters.relationshipGrowth = target.snapshot.relationshipSummary
  return appendPlayableVersion(projectId, { reason: 'restore', restoredFrom: target.version, name: `${session.spec.title} · Restore v${session.playableVersions.length + 1}` })
}

export function createReleaseDraftForProject(projectId: string): ReleaseDraft | null {
  const session = getProject(projectId)
  if (!session) return null
  const playable = getCurrentPlayable(session)
  const version = session.releases.length + 1
  const draft: ReleaseDraft = {
    version,
    name: `${session.spec.title} · ${version === 1 ? 'First Release' : `Release ${version}`}`,
    description: version === 1 ? session.spec.buildTarget.goal : '基于最新稳定 Playable 的正式版本。',
    basedOnPlayable: playable?.version ?? 0,
    basedOnGameDesign: session.designVersion,
    basedOnGameSpec: session.specVersion,
  }
  session.releaseDraft = draft
  touchProject(session)
  return draft
}

export function touchProject(session: ProjectSession): void {
  session.updatedAt = Date.now()
  persistProjectStore()
}

export function createProjectSession(design: ConfirmedGameDesign, projectId?: string): ProjectSession {
  projectCounter += 1
  const now = Date.now()
  return {
    id: projectId ?? `project-${now}-${projectCounter}`,
    backendProjectId: projectId ?? null,
    createdAt: now,
    updatedAt: now,
    design,
    spec: createGameSpecFixture(design),
    designVersion: 1,
    specVersion: 1,
    playableVersions: [],
    releases: [],
    phase: 'generating',
    messages: [{
      id: 'spec-start',
      role: 'ai',
      text: '游戏设计已经确认。我正在把它整理成第一版可以实际制作的游戏规格，并会主动控制范围，避免第一版过大。',
    }],
    changePlan: null,
    releasePhase: 'review',
    releaseDraft: {
      version: 1,
      name: `${design.projectTitle} v1`,
      description: '',
      basedOnPlayable: 1,
      basedOnGameDesign: 1,
      basedOnGameSpec: 1,
    },
    pendingContext: null,
    reuseDecisions: {},
    reuseSpecVersion: 1,
    matchedResources: {},
    relationshipSnapshot: null,
    resourceBridgeAcknowledged: false,
    resourceBatches: {},
    designStatus: 'draft',
    gamespecStatus: 'missing',
    canonicalGameSpec: null,
    gamespecRevisionId: null,
    gamespecGitCommit: null,
    remoteBuild: null,
  }
}

function restoreProjectStore(): void {
  if (!canUseProjectStorage()) return
  try {
    const raw = window.localStorage.getItem(PROJECT_STORE_STORAGE_KEY)
    if (!raw) return
    const parsed = JSON.parse(raw) as Partial<PersistedProjectStore>
    if (parsed.version !== 1 || !Array.isArray(parsed.projects)) return

    for (const snapshot of parsed.projects) {
      if (!snapshot || typeof snapshot !== 'object' || typeof snapshot.id !== 'string' || !snapshot.design) continue
      const session = createProjectSession(snapshot.design)
      Object.assign(session, snapshot)
      session.backendProjectId = typeof snapshot.backendProjectId === 'string' ? snapshot.backendProjectId : null
      projectStore.projects.push(session)
    }
  } catch {
    // Ignore malformed snapshots and fall back to API state.
  }
}

restoreProjectStore()

export function createProject(design: ConfirmedGameDesign, projectId?: string): ProjectSession {
  const session = createProjectSession(design, projectId)
  projectStore.projects.push(session)
  projectStore.activeProjectId = session.id
  persistProjectStore()
  return session
}

export function openProject(id: string): ProjectSession | null {
  const session = getProject(id)
  if (!session) return null
  projectStore.activeProjectId = session.id
  return session
}

export function bindBackendProject(projectId: string): void {
  const session = getProject(projectId)
  if (!session) return
  session.backendProjectId = projectId
  touchProject(session)
}

export function setProjectDesignStatus(projectId: string, status: ProjectSession['designStatus']): void {
  const session = getProject(projectId)
  if (!session) return
  session.designStatus = status
  touchProject(session)
}

export function setProjectGameSpecState(
  projectId: string,
  state: { status: Exclude<ProjectSession['gamespecStatus'], 'missing'>; revisionId: string; spec: CreatorGameSpec; gitCommit?: string | null },
): void {
  const session = getProject(projectId)
  if (!session) return
  session.gamespecStatus = state.status
  session.gamespecRevisionId = state.revisionId
  session.gamespecGitCommit = state.gitCommit ?? session.gamespecGitCommit
  session.canonicalGameSpec = state.spec
  touchProject(session)
}

const REMOTE_BUILD_TERMINAL_STATUSES = new Set(['succeeded', 'failed', 'cancelled', 'timed_out', 'invalid_output', 'unsupported'])
const remoteBuildPollers = new Map<string, number>()

function clearRemoteBuildPoller(projectId: string): void {
  const timer = remoteBuildPollers.get(projectId)
  if (timer !== undefined) window.clearInterval(timer)
  remoteBuildPollers.delete(projectId)
}

function applyRemoteBuildResponse(projectId: string, response: BuildResponse): void {
  const session = getProject(projectId)
  if (!session) return
  const previous = session.remoteBuild
  applyRemoteBuildState(session, {
    ...previous,
    buildId: response.build_id,
    runId: response.run_id,
    status: response.status,
    candidateId: response.candidate_id,
    artifactPath: response.artifact_path,
    errorCode: response.error_code,
    errorMessage: response.error_message,
    buildContextHash: response.build_context_hash,
  })
}

function applyRemoteBuildState(session: ProjectSession, state: RemoteBuildState): void {
  session.remoteBuild = state
  if (state.playableVersion) {
    session.phase = 'playable_ready'
    clearRemoteBuildPoller(session.id)
  } else if (state.status === 'succeeded' && state.candidateId) {
    // A successful build creates a Candidate only. Promotion remains a Human Gate.
    session.phase = 'candidate_ready'
    clearRemoteBuildPoller(session.id)
  } else if (REMOTE_BUILD_TERMINAL_STATUSES.has(state.status)) {
    session.phase = 'build_error'
    clearRemoteBuildPoller(session.id)
  } else {
    session.phase = 'building_foundation'
  }
  touchProject(session)
}

export function hydrateRemoteBuild(projectId: string, state: RemoteBuildState): void {
  const session = getProject(projectId)
  if (!session) return
  applyRemoteBuildState(session, state)
}

export async function refreshRemoteBuild(projectId: string): Promise<void> {
  const session = getProject(projectId)
  const buildId = session?.remoteBuild?.buildId
  if (!session || !session.backendProjectId || !buildId) return
  try {
    const response = await getProjectBuild(buildId)
    applyRemoteBuildResponse(projectId, response)
  } catch {
    // A just-created build may not be visible until its first transaction commits.
    // Keep the existing working state and let the next poll retry.
  }
}

function startRemoteBuildPolling(projectId: string): void {
  if (remoteBuildPollers.has(projectId)) return
  const timer = window.setInterval(() => {
    void refreshRemoteBuild(projectId)
  }, 2000)
  remoteBuildPollers.set(projectId, timer)
}

export async function startRemoteBuild(projectId: string): Promise<void> {
  const session = getProject(projectId)
  if (!session?.backendProjectId) return
  const existing = session.remoteBuild
  if (existing && !REMOTE_BUILD_TERMINAL_STATUSES.has(existing.status)) return

  const buildId = existing?.buildId ?? crypto.randomUUID()
  const runId = existing?.runId ?? `run-${buildId}`
  session.remoteBuild = {
    buildId,
    runId,
    status: 'running',
    candidateId: null,
    artifactPath: null,
    errorCode: null,
    errorMessage: null,
  }
  session.phase = 'build_starting'
  touchProject(session)
  startRemoteBuildPolling(projectId)

  try {
    const response = await createProjectBuild(session.backendProjectId, {
      buildId,
      runId,
      requestText: '根据已确认的 GameSpec 创建第一个可试玩版本，并生成真实 index.html。',
    })
    applyRemoteBuildResponse(projectId, response)
  } catch (cause) {
    const current = getProject(projectId)
    if (!current) return
    current.remoteBuild = {
      buildId,
      runId,
      status: 'failed',
      candidateId: null,
      artifactPath: null,
      errorCode: cause instanceof ApiClientError ? cause.code : 'build_request_failed',
      errorMessage: cause instanceof ApiClientError ? cause.message : '真实 Build 请求失败。',
    }
    current.phase = 'build_error'
    clearRemoteBuildPoller(projectId)
    touchProject(current)
  }
}

export async function cancelRemoteBuild(projectId: string): Promise<void> {
  const session = getProject(projectId)
  const buildId = session?.remoteBuild?.buildId
  if (!session?.backendProjectId || !buildId) return
  try {
    const response = await cancelProjectBuild(buildId)
    applyRemoteBuildResponse(projectId, response)
  } catch (cause) {
    session.messages.push({
      id: `build-cancel-error-${Date.now()}`,
      role: 'system',
      text: cause instanceof ApiClientError ? cause.message : '暂时无法取消真实 Build，请稍后重试。',
    })
    touchProject(session)
  }
}

export async function testRemoteCandidate(projectId: string): Promise<void> {
  const session = getProject(projectId)
  const candidateId = session?.remoteBuild?.candidateId
  if (!session?.remoteBuild || !candidateId || session.remoteBuild.testRunning) return
  session.remoteBuild.testRunning = true
  session.remoteBuild.testError = null
  touchProject(session)
  try {
    const response = await testBuildCandidate(candidateId)
    session.remoteBuild.testGateStatus = response.test_gate_status
    session.remoteBuild.testReport = response.report
    session.remoteBuild.candidatePreviewUrl = response.test_gate_status === 'ready'
      ? candidatePreviewUrl(projectId, candidateId)
      : null
  } catch (cause) {
    session.remoteBuild.testError = cause instanceof ApiClientError ? cause.message : '平台验证暂时无法完成。'
  } finally {
    session.remoteBuild.testRunning = false
    touchProject(session)
  }
}

export async function refreshRemoteCandidateTest(projectId: string): Promise<void> {
  const session = getProject(projectId)
  const candidateId = session?.remoteBuild?.candidateId
  if (!session?.remoteBuild || !candidateId || session.remoteBuild.testGateStatus === 'untested') return
  try {
    const response = await getBuildCandidateTestReport(candidateId)
    session.remoteBuild.testGateStatus = response.test_gate_status
    session.remoteBuild.testReport = response.report
    session.remoteBuild.candidatePreviewUrl = response.test_gate_status === 'ready'
      ? candidatePreviewUrl(projectId, candidateId)
      : null
    session.remoteBuild.testError = null
  } catch (cause) {
    session.remoteBuild.testError = cause instanceof ApiClientError ? cause.message : '暂时无法读取平台验证证据。'
  }
  touchProject(session)
}

export async function refreshRemoteHumanReview(projectId: string): Promise<void> {
  const session = getProject(projectId)
  const candidateId = session?.remoteBuild?.candidateId
  if (!session?.remoteBuild || !candidateId) return
  try {
    session.remoteBuild.humanReview = await getHumanPlayReview(candidateId)
    session.remoteBuild.reviewError = null
  } catch (cause) {
    if (cause instanceof ApiClientError && cause.code === 'human_play_review_not_found') {
      session.remoteBuild.humanReview = null
      session.remoteBuild.reviewError = null
    } else {
      session.remoteBuild.reviewError = cause instanceof ApiClientError ? cause.message : '暂时无法读取人工试玩状态。'
    }
  }
  touchProject(session)
}

export async function reviewRemoteCandidate(
  projectId: string,
  decision: 'accepted' | 'rejected',
  notes = '',
): Promise<void> {
  const session = getProject(projectId)
  const candidateId = session?.remoteBuild?.candidateId
  if (!session?.remoteBuild || !candidateId || session.remoteBuild.reviewRunning) return
  session.remoteBuild.reviewRunning = true
  session.remoteBuild.reviewError = null
  touchProject(session)
  try {
    session.remoteBuild.humanReview = await recordHumanPlayReview(candidateId, { decision, notes })
  } catch (cause) {
    session.remoteBuild.reviewError = cause instanceof ApiClientError ? cause.message : '暂时无法保存人工试玩决定。'
  } finally {
    session.remoteBuild.reviewRunning = false
    touchProject(session)
  }
}

export async function promoteRemoteCandidate(projectId: string): Promise<void> {
  const session = getProject(projectId)
  const remote = session?.remoteBuild
  const candidateId = remote?.candidateId
  if (!session || !remote || !candidateId || remote.promoteRunning || remote.testGateStatus !== 'ready') return
  remote.promoteRunning = true
  remote.promoteError = null
  touchProject(session)
  try {
    const gitCommit = session.gamespecGitCommit || remote.buildContextHash || remote.buildId
    const version = await promoteBuildCandidate(candidateId, gitCommit)
    remote.playableVersion = version
    remote.previewUrl = playablePreviewUrl(projectId, version.version_id)
    // The candidate endpoint is intentionally no longer playable after
    // promotion. Drop the review-only URL so a persisted session cannot
    // request it while the Playable preview is being restored.
    remote.candidatePreviewUrl = null
    remote.promoteError = null
    session.phase = 'playable_ready'
  } catch (cause) {
    remote.promoteError = cause instanceof ApiClientError ? cause.message : '暂时无法设为当前 Playable。'
  } finally {
    remote.promoteRunning = false
    touchProject(session)
  }
}

export async function refreshRemotePlayable(projectId: string): Promise<void> {
  const session = getProject(projectId)
  if (!session?.backendProjectId) return
  try {
    const versions = await listPlayableVersions(projectId)
    const current = versions.find((version) => version.is_current) ?? versions[0]
    if (!current) return
    if (!session.remoteBuild) {
      session.remoteBuild = {
        buildId: '',
        runId: '',
        status: 'succeeded',
        candidateId: current.candidate_id,
        artifactPath: current.artifact_path,
        errorCode: null,
        errorMessage: null,
      }
    }
    session.remoteBuild.playableVersion = current
    session.remoteBuild.previewUrl = playablePreviewUrl(projectId, current.version_id)
    session.remoteBuild.candidatePreviewUrl = null
    session.phase = 'playable_ready'
  } catch (cause) {
    if (session.remoteBuild) session.remoteBuild.promoteError = cause instanceof ApiClientError ? cause.message : '暂时无法读取 Playable 版本。'
  }
  touchProject(session)
}

export async function rebuildRemoteCandidate(projectId: string): Promise<void> {
  const session = getProject(projectId)
  const parentCandidateId = session?.remoteBuild?.candidateId
  if (!session?.backendProjectId || !parentCandidateId) return
  session.remoteBuild = null
  await startRemoteBuild(projectId)
  const updated = getProject(projectId)
  const replacementCandidateId = updated?.remoteBuild?.candidateId
  if (!updated?.remoteBuild || updated.remoteBuild.status !== 'succeeded' || !replacementCandidateId) return
  try {
    await linkBuildCandidateRepair(parentCandidateId, replacementCandidateId)
  } catch (cause) {
    updated.remoteBuild.testError = cause instanceof ApiClientError ? cause.message : '新 Candidate 已生成，但暂时无法记录修复来源。'
    touchProject(updated)
  }
}

type TimerJobKey =
  | 'generation'
  | 'build'
  | 'change'
  | 'publish'
  | `resource-save:${string}:${string}`

const timers = new Map<string, Map<TimerJobKey, number>>()

export function scheduleJob(projectId: string, key: TimerJobKey, job: () => void, delay: number): void {
  clearJob(projectId, key)
  let projectTimers = timers.get(projectId)
  if (!projectTimers) {
    projectTimers = new Map()
    timers.set(projectId, projectTimers)
  }
  const jobs = projectTimers
  const timeoutId = window.setTimeout(() => {
    jobs.delete(key)
    job()
  }, delay)
  projectTimers.set(key, timeoutId)
}

export function clearJob(projectId: string, key: TimerJobKey): void {
  const projectTimers = timers.get(projectId)
  if (!projectTimers) return
  const timeoutId = projectTimers.get(key)
  if (timeoutId !== undefined) window.clearTimeout(timeoutId)
  projectTimers.delete(key)
}

export type WorkspaceDebugFlags = {
  specError: boolean
  buildError: boolean
  scopeError: boolean
  publishError: boolean
}

const defaultDebugFlags: WorkspaceDebugFlags = {
  specError: false,
  buildError: false,
  scopeError: false,
  publishError: false,
}

export type DemoErrorFlags = WorkspaceDebugFlags & {
  kickoffError: boolean
}

export const runtimeConfig = reactive({
  kickoffError: false,
  projectDebugFlags: new Map<string, WorkspaceDebugFlags>(),
})

export function setProjectDebugFlags(projectId: string, flags: Partial<WorkspaceDebugFlags>): void {
  runtimeConfig.projectDebugFlags.set(projectId, { ...defaultDebugFlags, ...flags })
}

export function getProjectDebugFlags(projectId: string): WorkspaceDebugFlags {
  return runtimeConfig.projectDebugFlags.get(projectId) ?? defaultDebugFlags
}

export function configureDemoRuntime(flags: Partial<DemoErrorFlags>): void {
  runtimeConfig.kickoffError = flags.kickoffError ?? false
}

export function resetDemoRuntime(): void {
  runtimeConfig.kickoffError = false
  runtimeConfig.projectDebugFlags.clear()
}

type ErrorInjectionKind = 'generation' | 'build' | 'scope' | 'publish'
const consumedErrorInjections = new Map<string, Set<ErrorInjectionKind>>()

function consumeErrorInjection(projectId: string, kind: ErrorInjectionKind): boolean {
  let consumed = consumedErrorInjections.get(projectId)
  if (!consumed) {
    consumed = new Set()
    consumedErrorInjections.set(projectId, consumed)
  }
  if (consumed.has(kind)) return false
  consumed.add(kind)
  return true
}

export function completeGeneration(projectId: string): void {
  const session = getProject(projectId)
  if (!session) return
  if (getProjectDebugFlags(projectId).specError && consumeErrorInjection(projectId, 'generation')) {
    session.phase = 'generation_error'
    touchProject(session)
    return
  }
  session.phase = 'review'
  if (!session.messages.some((message) => message.id === 'spec-ready')) session.messages.push({
    id: 'spec-ready',
    role: 'ai',
    text: session.design.scenarioId === 'coffee-shop'
      ? '第一版 GameSpec 已经整理好了。我保留了咖啡经营和人物关系的核心，并把第一版收敛成可以先完成订单、认识店员与常客的可玩闭环。你可以直接确认，也可以选择任何 Section 让我调整。'
      : '第一版 GameSpec 已经整理好了。我保留了你确认的关系成长核心，同时把完整多代经营收敛成一个可以先做出来试玩的版本。你可以直接确认，也可以选择任何 Section 让我调整。',
  })
  refreshResourceMatches(projectId)
  touchProject(session)
}

export function startGeneration(projectId: string): void {
  const session = getProject(projectId)
  if (!session) return
  session.phase = 'generating'
  touchProject(session)
  scheduleJob(projectId, 'generation', () => completeGeneration(projectId), 1250)
}

export function requestSpecRevision(projectId: string, context: SpecContext, text: string): void {
  const session = getProject(projectId)
  if (!session || session.phase !== 'review') return
  session.pendingContext = context
  session.messages.push({ id: `user-${Date.now()}`, role: 'user', text })
  session.phase = 'revising'
  touchProject(session)
  scheduleJob(projectId, 'generation', () => {
    session.phase = 'review'
    session.messages.push({
      id: `proposal-${Date.now()}`,
      role: 'ai',
      text: context.key === 'characters'
        ? `可以。我会把 ${session.spec.characters.npcName} 的关系行为调整成“陌生 → 熟悉 → 亲近”，并让每个阶段使用不同的对话池。`
        : `可以。我会更新 ${context.label}，同时保持 First Playable 的范围不继续膨胀。`,
      action: 'apply-revision',
    })
    touchProject(session)
  }, 820)
}

export function applySpecRevision(projectId: string): void {
  const session = getProject(projectId)
  if (!session) return
  const context = session.pendingContext
  if (!context) return
  session.messages = session.messages.map((message) => (
    message.action === 'apply-revision' ? { ...message, action: undefined } : message
  ))
  const spec = session.spec
  if (context.key === 'characters') {
    spec.characters.dialogueStates = ['陌生', '熟悉', '亲近']
    if (!spec.characters.npcBehaviors.includes('按关系阶段切换对话池')) spec.characters.npcBehaviors.push('按关系阶段切换对话池')
    const relationshipValidation = `${spec.characters.npcName} 的对话会随关系阶段变化`
    if (!spec.validation.includes(relationshipValidation)) spec.validation.push(relationshipValidation)
  } else if (context.key === 'gameplay' && !spec.gameplay.actions.includes('关系事件选择')) {
    spec.gameplay.actions.push('关系事件选择')
  } else if (context.key === 'scope' && !spec.scope.included.includes('三阶段 NPC 对话')) {
    spec.scope.included.push('三阶段 NPC 对话')
  } else if (context.key === 'validation' && !spec.validation.includes('所有关键状态变化都能被玩家看见')) {
    spec.validation.push('所有关键状态变化都能被玩家看见')
  }
  if (!spec.updatedSections.includes(context.key)) spec.updatedSections.push(context.key)
  spec.draftLabel = 'Draft updated · v1'
  session.messages.push({ id: `applied-${Date.now()}`, role: 'system', text: `${context.label} 已更新到 GameSpec v1 Draft。` })
  session.pendingContext = null
  refreshResourceMatches(projectId)
  touchProject(session)
}

export function requestSpecConfirmation(projectId: string): void {
  const session = getProject(projectId)
  if (!session || session.phase !== 'review') return
  session.phase = 'confirming'
  touchProject(session)
}

export function confirmSpecAndStartBuild(projectId: string): void {
  const session = getProject(projectId)
  if (!session) return
  session.phase = 'spec_confirmed'
  touchProject(session)
  scheduleJob(projectId, 'generation', () => {
    startBuildTimeline(projectId)
  }, 820)
}

const buildSequence: BuildPhase[] = [
  'building_foundation', 'building_core', 'building_interaction',
  'building_presentation', 'building_progression', 'validating',
  'auto_fixing', 'validating_complete', 'playable_ready',
]

function advanceBuild(projectId: string, index: number): void {
  if (index >= buildSequence.length) return
  const session = getProject(projectId)
  if (!session) return
  const next = buildSequence[index]!
  const delay = next === 'auto_fixing' ? 1150 : next === 'validating_complete' ? 1050 : 850
  scheduleJob(projectId, 'build', () => {
    if (next === 'building_presentation' && getProjectDebugFlags(projectId).buildError && consumeErrorInjection(projectId, 'build')) {
      session.phase = 'build_error'
      touchProject(session)
      return
    }
    session.phase = next
    touchProject(session)
    if (next === 'playable_ready') {
      if (!getCurrentPlayable(session)) appendPlayableVersion(projectId, { reason: 'initial', name: `${session.spec.title} · First Playable` })
      scheduleJob(projectId, 'build', () => {
        session.phase = 'showing_recommendations'
        touchProject(session)
      }, 650)
      return
    }
    advanceBuild(projectId, index + 1)
  }, delay)
}

export function startBuildTimeline(projectId: string): void {
  const session = getProject(projectId)
  if (!session) return
  session.phase = 'build_starting'
  touchProject(session)
  advanceBuild(projectId, 0)
}

const cancellableBuildPhases: BuildPhase[] = [
  'build_starting', 'building_foundation', 'building_core', 'building_interaction',
  'building_presentation', 'building_progression', 'validating', 'auto_fixing', 'validating_complete',
]

export function cancelBuild(projectId: string): void {
  const session = getProject(projectId)
  if (!session || !cancellableBuildPhases.includes(session.phase as BuildPhase)) return
  clearJob(projectId, 'generation')
  clearJob(projectId, 'build')
  session.phase = 'review'
  session.messages.push({ id: `build-cancelled-${Date.now()}`, role: 'system', text: 'Build 已取消。当前 GameSpec 保持不变，可以调整后重新确认。' })
  touchProject(session)
}

export function retryBuild(projectId: string): void {
  const session = getProject(projectId)
  if (!session || session.phase !== 'build_error') return
  session.phase = 'building_presentation'
  touchProject(session)
  advanceBuild(projectId, 4)
}

export function requestChange(projectId: string, source: ChangeSource, request?: string): void {
  const session = getProject(projectId)
  if (!session) return
  session.changePlan = createChangePlan(source, request)
  session.phase = 'change_requested'
  touchProject(session)
  scheduleJob(projectId, 'change', () => {
    session.phase = 'analyzing_change'
    touchProject(session)
    scheduleJob(projectId, 'change', () => {
      session.phase = 'change_review'
      touchProject(session)
    }, 900)
  }, 260)
}

export function cancelChange(projectId: string): void {
  const session = getProject(projectId)
  if (!session) return
  clearJob(projectId, 'change')
  session.changePlan = null
  session.phase = 'showing_recommendations'
  touchProject(session)
}

const changeSequence: ChangePhase[] = [
  'reusing_unaffected_content', 'applying_gameplay_change', 'applying_visual_change',
  'checking_scope', 'building_working_version', 'validating_change',
  'auto_fixing_change', 'validation_complete_change', 'playable_v2_ready',
]

function advanceChange(projectId: string, index: number): void {
  if (index >= changeSequence.length) return
  const session = getProject(projectId)
  if (!session) return
  const next = changeSequence[index]!
  const delay = next === 'auto_fixing_change' ? 1100 : next === 'validation_complete_change' ? 950 : 800
  scheduleJob(projectId, 'change', () => {
    if (next === 'checking_scope' && getProjectDebugFlags(projectId).scopeError && consumeErrorInjection(projectId, 'scope')) {
      session.phase = 'scope_violation'
      touchProject(session)
      return
    }
    session.phase = next
    touchProject(session)
    if (next === 'playable_v2_ready') {
      appendPlayableVersion(projectId, { reason: 'change', name: `${session.spec.title} · Playable v${session.playableVersions.length + 1}` })
      return
    }
    advanceChange(projectId, index + 1)
  }, delay)
}

export function applyControlledChange(projectId: string): void {
  const session = getProject(projectId)
  if (!session || !session.changePlan || session.phase !== 'change_review') return
  session.phase = 'preparing_working_build'
  touchProject(session)
  advanceChange(projectId, 0)
}

export function retryScopeViolation(projectId: string): void {
  const session = getProject(projectId)
  if (!session || session.phase !== 'scope_violation') return
  session.phase = 'reusing_unaffected_content'
  touchProject(session)
  advanceChange(projectId, 1)
}

export function setWorkspacePhase(projectId: string, nextPhase: WorkspacePhase): void {
  const session = getProject(projectId)
  if (!session) return
  session.phase = nextPhase
  touchProject(session)
}

export function acknowledgeResourceBridge(projectId: string): void {
  const session = getProject(projectId)
  if (!session) return
  session.resourceBridgeAcknowledged = true
  touchProject(session)
}

export function seedChangeDemo(projectId: string, nextPhase: 'showing_recommendations' | 'playable_v2_ready'): void {
  const session = getProject(projectId)
  if (!session) return
  clearJob(projectId, 'change')
  session.changePlan = createChangePlan('suggested_next_step')
  session.phase = nextPhase
  touchProject(session)
}

export function prepareReleaseReview(projectId: string): void {
  const session = getProject(projectId)
  if (!session) return
  session.releasePhase = 'review'
  createReleaseDraftForProject(projectId)
  touchProject(session)
}

export function seedPublishedRelease(projectId: string): ReleaseRecord | null {
  const session = getProject(projectId)
  if (!session) return null
  const draft = createReleaseDraftForProject(projectId)
  if (!draft) return null
  const release: ReleaseRecord = {
    ...draft,
    id: `release-v${draft.version}`,
    status: 'published',
    createdAt: '刚刚',
  }
  session.releases.push(release)
  session.resourceBatches[release.id] = createResourceCandidates(session, release).map((candidate) => ({ candidate, state: 'pending' }))
  session.releasePhase = 'success'
  touchProject(session)
  return release
}

export function updateReleaseDraft(projectId: string, patch: Partial<ReleaseDraft>): void {
  const session = getProject(projectId)
  if (!session) return
  Object.assign(session.releaseDraft, patch)
  touchProject(session)
}

export function publishRelease(projectId: string): void {
  const session = getProject(projectId)
  if (!session || (session.releasePhase !== 'review' && session.releasePhase !== 'error')) return
  session.releasePhase = 'publishing'
  touchProject(session)
  scheduleJob(projectId, 'publish', () => {
    if (getProjectDebugFlags(projectId).publishError && consumeErrorInjection(projectId, 'publish')) {
      session.releasePhase = 'error'
      touchProject(session)
      return
    }
    seedPublishedRelease(projectId)
  }, 900)
}
