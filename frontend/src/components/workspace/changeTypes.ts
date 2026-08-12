export type ChangePhase =
  | 'showing_recommendations'
  | 'playing_v1'
  | 'change_requested'
  | 'analyzing_change'
  | 'change_review'
  | 'preparing_working_build'
  | 'reusing_unaffected_content'
  | 'applying_gameplay_change'
  | 'applying_visual_change'
  | 'checking_scope'
  | 'scope_violation'
  | 'building_working_version'
  | 'validating_change'
  | 'auto_fixing_change'
  | 'validation_complete_change'
  | 'playable_v2_ready'
  | 'version_history'

export type ChangeSource = 'suggested_next_step' | 'natural_language' | 'gamespec_direct_edit'
export type ChangeType = 'Documentation' | 'Parameter' | 'Gameplay' | 'Visual'
export type ChangeProgressStatus = 'completed' | 'active' | 'upcoming' | 'failed'

export type ChangeItem = {
  id: string
  title: string
  userType: string
  current?: string
  next: string
}

export type ArtifactImpact = {
  label: string
  detail: string
  technicalScope: string
}

export type ChangeProgressStep = {
  id: 'prepare' | 'reuse' | 'gameplay' | 'visual' | 'scope' | 'build' | 'validation'
  label: string
  detail: string
}

export type ChangeValidationCheck = {
  id: string
  label: string
}

export type ChangePlan = {
  id: string
  source: ChangeSource
  sourceLabel: string
  originalRequest: string
  summary: string
  interpretation: string
  changeTypes: ChangeType[]
  changes: ChangeItem[]
  affected: ArtifactImpact[]
  reused: string[]
  requiresBuild: boolean
  requiresValidation: boolean
  buildReason: string
  scopeExpected: string[]
  progress: ChangeProgressStep[]
  changedChecks: ChangeValidationCheck[]
  regressionChecks: ChangeValidationCheck[]
}
