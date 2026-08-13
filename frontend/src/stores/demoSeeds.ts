import { createDemoConfirmedDesign, createResourceReuseConfirmedDesign } from '../components/workspace/gameSpecFixture'
import type { ResourceCandidate } from '../components/resources/resourceTypes'
import type { ReleaseRecord } from '../components/workspace/releaseTypes'
import {
  appendPlayableVersion,
  completeGeneration,
  configureDemoRuntime,
  createProject,
  createProjectSession,
  createResourceCandidates,
  prepareReleaseReview,
  projectStore,
  resetDemoRuntime,
  resetProjectStore,
  seedChangeDemo,
  seedPublishedRelease,
  setProjectDebugFlags,
  startBuildTimeline,
  startGeneration,
  type DemoErrorFlags,
} from './projectStore'

export type DemoSeedName =
  | 'gamespec'
  | 'build'
  | 'change'
  | 'publish'
  | 'resource-reuse'
  | 'resources'
  | 'my-resources'

export type AppSurface = 'projects' | 'workspace' | 'resources' | 'review'

const noErrors: DemoErrorFlags = {
  specError: false,
  buildError: false,
  scopeError: false,
  publishError: false,
  kickoffError: false,
}

function createSeedRelease(session = createProjectSession(createDemoConfirmedDesign())): ReleaseRecord {
  return {
    id: 'release-v1',
    version: 1,
    name: `${session.spec.title} · First Release`,
    description: session.spec.buildTarget.goal,
    basedOnPlayable: 1,
    basedOnGameDesign: session.designVersion,
    basedOnGameSpec: session.specVersion,
    status: 'published',
    createdAt: '刚刚',
  }
}

function createSavedRelationshipResource(): ResourceCandidate {
  const source = createProjectSession(createDemoConfirmedDesign())
  const resource = createResourceCandidates(source, createSeedRelease(source)).find((candidate) => candidate.id === 'relationship-system')
  if (!resource) throw new Error('Demo relationship resource is missing')
  resource.status = 'saved'
  return resource
}

function createReadyProject(flags: DemoErrorFlags) {
  const session = createProject(createDemoConfirmedDesign())
  setProjectDebugFlags(session.id, flags)
  completeGeneration(session.id)
  return session
}

/**
 * Seed the store from the demo entrypoint. Components only render the seeded
 * session and keep their short-lived UI state locally.
 */
export function seedDemo(name: DemoSeedName, inputFlags: Partial<DemoErrorFlags> = {}): AppSurface {
  const flags = { ...noErrors, ...inputFlags }
  resetProjectStore()
  resetDemoRuntime()
  configureDemoRuntime(flags)

  if (name === 'my-resources') {
    projectStore.savedResources.push(createSavedRelationshipResource())
    return 'resources'
  }

  if (name === 'resource-reuse') {
    projectStore.savedResources.push(createSavedRelationshipResource())
    const session = createProject(createResourceReuseConfirmedDesign())
    setProjectDebugFlags(session.id, flags)
    completeGeneration(session.id)
    return 'workspace'
  }

  if (name === 'gamespec') {
    const session = createProject(createDemoConfirmedDesign())
    setProjectDebugFlags(session.id, flags)
    startGeneration(session.id)
    return 'workspace'
  }

  const session = createReadyProject(flags)
  appendPlayableVersion(session.id, { reason: 'initial', name: `${session.spec.title} · First Playable` })

  if (name === 'build') {
    startBuildTimeline(session.id)
    return 'workspace'
  }

  seedChangeDemo(session.id, name === 'change' ? 'showing_recommendations' : 'playable_v2_ready')

  if (name === 'change') return 'workspace'

  appendPlayableVersion(session.id, { reason: 'change', name: `${session.spec.title} · Playable v2` })
  prepareReleaseReview(session.id)

  if (name === 'publish') return 'workspace'

  const release = seedPublishedRelease(session.id)
  if (!release) throw new Error('Demo release could not be created')
  return 'review'
}
