import { reactive } from 'vue'
import type { ConfirmedGameDesign } from '../components/kickoff/kickoffTypes'
import type { ResourceBatchItem, ResourceCandidate } from '../components/resources/resourceTypes'
import type { ChangePlan } from '../components/workspace/changeTypes'
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
    messages: [],
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
