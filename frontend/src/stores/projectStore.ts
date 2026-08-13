import { reactive } from 'vue'
import type { ConfirmedGameDesign } from '../components/kickoff/kickoffTypes'
import type { ResourceBatchItem, ResourceCandidate } from '../components/resources/resourceTypes'
import type { BuildPhase } from '../components/workspace/buildTypes'
import { createChangePlan } from '../components/workspace/changeFixture'
import type { ChangePhase, ChangePlan, ChangeSource } from '../components/workspace/changeTypes'
import { createGameSpecFixture } from '../components/workspace/gameSpecFixture'
import type { ReleaseDraft, ReleasePhase, ReleaseRecord } from '../components/workspace/releaseTypes'
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

export function touchProject(session: ProjectSession): void {
  session.updatedAt = Date.now()
}

export function createProjectSession(design: ConfirmedGameDesign): ProjectSession {
  projectCounter += 1
  const now = Date.now()
  return {
    id: `project-${now}-${projectCounter}`,
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
  }
}

export function createProject(design: ConfirmedGameDesign): ProjectSession {
  const session = createProjectSession(design)
  projectStore.projects.push(session)
  projectStore.activeProjectId = session.id
  return session
}

export function openProject(id: string): ProjectSession | null {
  const session = getProject(id)
  if (!session) return null
  projectStore.activeProjectId = session.id
  return session
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

const debugFlags: WorkspaceDebugFlags = {
  specError: false,
  buildError: false,
  scopeError: false,
  publishError: false,
}

export function setDebugFlags(flags: Partial<WorkspaceDebugFlags>): void {
  Object.assign(debugFlags, flags)
}

export function getDebugFlags(): WorkspaceDebugFlags {
  return debugFlags
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

export function startGeneration(projectId: string): void {
  const session = getProject(projectId)
  if (!session) return
  session.phase = 'generating'
  touchProject(session)
  scheduleJob(projectId, 'generation', () => {
    if (debugFlags.specError && consumeErrorInjection(projectId, 'generation')) {
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
    touchProject(session)
  }, 1250)
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
        ? '可以。我会把 Lucy 的关系行为调整成“陌生 → 熟悉 → 亲近”，并让每个阶段使用不同的对话池。'
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
    if (!spec.validation.includes('Lucy 的对话会随关系阶段变化')) spec.validation.push('Lucy 的对话会随关系阶段变化')
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
    if (next === 'building_presentation' && debugFlags.buildError && consumeErrorInjection(projectId, 'build')) {
      session.phase = 'build_error'
      touchProject(session)
      return
    }
    session.phase = next
    touchProject(session)
    if (next === 'playable_ready') {
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
    if (next === 'checking_scope' && debugFlags.scopeError && consumeErrorInjection(projectId, 'scope')) {
      session.phase = 'scope_violation'
      touchProject(session)
      return
    }
    session.phase = next
    touchProject(session)
    if (next === 'playable_v2_ready') return
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
  touchProject(session)
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
    if (debugFlags.publishError && consumeErrorInjection(projectId, 'publish')) {
      session.releasePhase = 'error'
      touchProject(session)
      return
    }
    const release = {
      ...session.releaseDraft,
      id: `release-v${session.releaseDraft.version}`,
      status: 'published' as const,
      createdAt: '刚刚',
    }
    session.releases.push(release)
    session.releasePhase = 'success'
    touchProject(session)
  }, 900)
}
