export type BuildPhase =
  | 'build_starting'
  | 'building_foundation'
  | 'building_core'
  | 'building_interaction'
  | 'building_presentation'
  | 'building_progression'
  | 'validating'
  | 'auto_fixing'
  | 'validating_complete'
  | 'playable_ready'
  | 'build_error'

export type BuildMilestoneId = 'foundation' | 'core' | 'interaction' | 'presentation' | 'progression' | 'validation'
export type MilestoneStatus = 'completed' | 'active' | 'upcoming' | 'failed'

export type BuildMilestone = {
  id: BuildMilestoneId
  number: string
  title: string
  summary: string
  completedMessage: string
  features: string[]
  gameSpecSource: string
  executionDetails: string[]
}

export type ValidationCheck = {
  id: string
  label: string
  source: string
}

export type BuildEvent = {
  id: string
  milestone: BuildMilestoneId
  label: string
  detail: string
}
