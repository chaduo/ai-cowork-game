export type ResourceCandidateType = 'gameplay' | 'ui' | 'visual'
export type ResourceCandidateStatus = 'pending' | 'saving' | 'saved' | 'ignored'
export type ResourceRecommendation = 'recommended' | 'worth_saving' | 'adjust_first'

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
}
