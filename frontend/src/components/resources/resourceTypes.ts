import type { SpecContext } from '../workspace/workspaceTypes'

export type ResourceCandidateType = 'gameplay' | 'ui' | 'visual'
export type ResourceCandidateStatus = 'pending' | 'saving' | 'saved' | 'ignored'
export type ResourceRecommendation = 'recommended' | 'worth_saving' | 'adjust_first'

export type ResourceBatchState = 'pending' | 'saving' | 'saved' | 'ignored'
export type ResourceBatchItem = { candidate: ResourceCandidate; state: ResourceBatchState }

export type ResourceMatchSignals = { section: SpecContext['key']; signals: string[] }

export type RelationshipReuseDefaults = {
  favorMin: number
  favorMax: number
  thresholds: number[]
  requestReward: number
  importantEventReward: number
}

export type ResourceCandidate = {
  id: string
  name: string
  type: ResourceCandidateType
  status: ResourceCandidateStatus
  recommendation: ResourceRecommendation
  cardSummary: string
  summary: string
  reuseReason: string
  reusableFor: string[]
  removedProjectContent: string[]
  included: string[]
  excluded: string[]
  configurableFields: { name: string; defaultValue: string; description: string }[]
  provenance: {
    projectName: string
    releaseVersion: string
    playableVersion: string
    gameSpecVersion: string
  }
  extractionChecks: {
    boundaryChecked: boolean
    projectSpecificContentRemoved: boolean
    parameterizable: boolean
  }
  matchSignals?: ResourceMatchSignals
  reuseDefaults?: RelationshipReuseDefaults
}
