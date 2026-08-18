import type { CreatorGameDesignDraft, DesignReadiness } from '../contracts/creatorGameDesign'
import type { CreatorGameSpec } from '../contracts/creatorGameSpec'
import type { ReleaseApiResponse } from '../contracts/releaseMapping'

export interface HealthResponse {
  status: 'ok'
  service: string
  version: string
}

export interface ProjectResponse {
  id: string
  name: string
  original_idea: string
  stage: string
  updated_at: string
  current_playable: {
    id: string
    number: number
    artifact_path: string
  } | null
  latest_release: {
    id: string
    number: number
    status: string
    playable_version_id: string
  } | null
  latest_build: {
    build_id: string
    run_id: string
    status: string
    candidate_id: string | null
    artifact_path: string | null
    error_code: string | null
    error_message: string | null
  } | null
  candidate_review: {
    candidate_id: string
    build_id: string
    run_id: string
    artifact_path: string
    test_gate_status: string
  } | null
}

export interface ApiErrorBody {
  error: {
    code: string
    message: string
    details: unknown[]
    request_id: string
  }
}

export interface DesignResponse {
  project_id: string
  design_id: string | null
  revision_id: string | null
  revision_number: number | null
  confirmed_revision_id: string | null
  confirmed_revision_number: number | null
  status: 'draft' | 'submitted' | 'confirmed'
  confirmed_at: string | null
  readiness: DesignReadiness
  draft: CreatorGameDesignDraft
  next_question?: {
    id: string
    prompt: string
    input_hint?: string
    choices: Array<{ id: string; title: string; description: string; recommended?: boolean }>
  } | null
}

export interface BrainstormInput {
  action: 'start' | 'answer' | 'free_text' | 'continue'
  question_id?: string
  answer_id?: string
  answer?: string
}

export interface GameSpecResponse {
  project_id: string
  revision_id: string
  revision_number: number
  status: 'draft' | 'confirmed' | 'superseded'
  confirmed_at: string | null
  git_commit: string | null
  source_design_revision_id: string | null
  validation_errors: Array<Record<string, unknown>>
  spec: CreatorGameSpec
}

export interface BuildResponse {
  build_id: string
  run_id: string
  project_id: string
  status: string
  attempt: number
  parent_build_id: string | null
  gamespec_revision_id: string
  baseline_playable_version_id: string | null
  operation: string
  request_text: string
  started_at: string | null
  ended_at: string | null
  candidate_id: string | null
  artifact_path: string | null
  diagnostics: Array<Record<string, unknown>>
  error_code: string | null
  error_message: string | null
  build_context_id: string | null
  build_context_hash: string | null
}

export interface CandidateEvidenceResponse {
  id: string
  kind: string
  status: string
  source: string
  severity: string
  expected: string
  observed: string
  artifact_ref: string
  details: Record<string, unknown>
}

export interface CandidateTestReportResponse {
  id: string
  candidate_id: string
  runtime_verdict: string
  platform_verdict: string
  status: string
  severity: string
  summary: string
  diagnostics: Array<Record<string, unknown>>
  created_at: string
  evidence: CandidateEvidenceResponse[]
}

export interface CandidateResponse {
  candidate_id: string
  project_id: string
  build_id: string
  build_status: string
  test_gate_status: string
  parent_candidate_id: string | null
  attempt: number
  repair_round: number
  source_playable_version_id: string | null
  report: CandidateTestReportResponse | null
}

export interface HumanPlayReviewResponse {
  id: string
  candidate_id: string
  decision: 'pending' | 'accepted' | 'rejected'
  notes: string
  amendment_status: string
  drift_status: string
  reviewed_at: string | null
}

export interface PlayableVersionResponse {
  version_id: string
  project_id: string
  candidate_id: string
  number: number
  parent_version_id: string | null
  test_report_id: string
  git_commit: string
  artifact_path: string
  artifact_checksum: string
  created_at: string
  is_current: boolean
}

export interface PublishReviewResponse {
  project_id: string
  eligible: boolean
  reason: string | null
  next_release_number: number
  playable_version_id: string | null
  playable_number: number | null
  game_design_revision_id: string | null
  gamespec_revision_id: string | null
  game_design_revision_number: number | null
  gamespec_revision_number: number | null
  artifact_path: string | null
  artifact_checksum: string | null
  git_commit: string | null
  existing_release: ReleaseApiResponse | null
}

export class ApiClientError extends Error {
  readonly code: string
  readonly requestId: string
  readonly details: unknown[]
  readonly status: number

  constructor(status: number, body: ApiErrorBody) {
    super(body.error.message)
    this.name = 'ApiClientError'
    this.status = status
    this.code = body.error.code
    this.requestId = body.error.request_id
    this.details = body.error.details
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, init)
  if (!response.ok) {
    const body = (await response.json()) as ApiErrorBody
    throw new ApiClientError(response.status, body)
  }
  return (await response.json()) as T
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/healthz')
}

export function createProjectRecord(input: { name: string; originalIdea: string }, idempotencyKey: string): Promise<ProjectResponse> {
  return request<ProjectResponse>('/v1/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Idempotency-Key': idempotencyKey },
    body: JSON.stringify({ name: input.name, original_idea: input.originalIdea }),
  })
}

export function getProjectRecord(projectId: string): Promise<ProjectResponse> {
  return request<ProjectResponse>(`/v1/projects/${encodeURIComponent(projectId)}`)
}

export function listProjectRecords(): Promise<ProjectResponse[]> {
  return request<ProjectResponse[]>('/v1/projects')
}

export function getProjectDesign(projectId: string): Promise<DesignResponse> {
  return request<DesignResponse>(`/v1/projects/${encodeURIComponent(projectId)}/design`)
}

export function saveProjectDesign(projectId: string, draft: CreatorGameDesignDraft): Promise<DesignResponse> {
  return request<DesignResponse>(`/v1/projects/${encodeURIComponent(projectId)}/design`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(draft),
  })
}

export function confirmProjectDesign(projectId: string): Promise<DesignResponse> {
  return request<DesignResponse>(`/v1/projects/${encodeURIComponent(projectId)}/design/confirm`, { method: 'POST' })
}

export function brainstormProjectDesign(projectId: string, input: BrainstormInput): Promise<DesignResponse> {
  return request<DesignResponse>(`/v1/projects/${encodeURIComponent(projectId)}/design/brainstorm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export function getProjectGameSpec(projectId: string): Promise<GameSpecResponse> {
  return request<GameSpecResponse>(`/v1/projects/${encodeURIComponent(projectId)}/gamespec`)
}

export function saveProjectGameSpec(projectId: string, spec: CreatorGameSpec): Promise<GameSpecResponse> {
  return request<GameSpecResponse>(`/v1/projects/${encodeURIComponent(projectId)}/gamespec`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(spec),
  })
}

export function confirmProjectGameSpec(projectId: string): Promise<GameSpecResponse> {
  return request<GameSpecResponse>(`/v1/projects/${encodeURIComponent(projectId)}/gamespec/confirm`, { method: 'POST' })
}

export function createProjectBuild(
  projectId: string,
  input: { buildId: string; runId: string; requestText?: string },
): Promise<BuildResponse> {
  return request<BuildResponse>(`/v1/projects/${encodeURIComponent(projectId)}/builds`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      build_id: input.buildId,
      run_id: input.runId,
      operation: 'create',
      request_text: input.requestText ?? '根据已确认的 GameSpec 创建第一个可试玩版本。',
    }),
  })
}

export function getProjectBuild(buildId: string): Promise<BuildResponse> {
  return request<BuildResponse>(`/v1/builds/${encodeURIComponent(buildId)}`)
}

export function cancelProjectBuild(buildId: string): Promise<BuildResponse> {
  return request<BuildResponse>(`/v1/builds/${encodeURIComponent(buildId)}/cancel`, { method: 'POST' })
}

export function testBuildCandidate(candidateId: string): Promise<CandidateResponse> {
  return request<CandidateResponse>(`/v1/candidates/${encodeURIComponent(candidateId)}/test`, { method: 'POST' })
}

export function getBuildCandidateTestReport(candidateId: string): Promise<CandidateResponse> {
  return request<CandidateResponse>(`/v1/candidates/${encodeURIComponent(candidateId)}/test-report`)
}

export function recordHumanPlayReview(
  candidateId: string,
  input: { decision: 'accepted' | 'rejected'; notes?: string },
): Promise<HumanPlayReviewResponse> {
  return request<HumanPlayReviewResponse>(`/v1/candidates/${encodeURIComponent(candidateId)}/human-play-review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      decision: input.decision,
      notes: input.notes ?? '',
      amendment_status: 'not_required',
      drift_status: 'clear',
    }),
  })
}

export function getHumanPlayReview(candidateId: string): Promise<HumanPlayReviewResponse> {
  return request<HumanPlayReviewResponse>(`/v1/candidates/${encodeURIComponent(candidateId)}/human-play-review`)
}

export function promoteBuildCandidate(candidateId: string, gitCommit: string): Promise<PlayableVersionResponse> {
  return request<PlayableVersionResponse>(`/v1/candidates/${encodeURIComponent(candidateId)}/promote`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ git_commit: gitCommit }),
  })
}

export function listPlayableVersions(projectId: string): Promise<PlayableVersionResponse[]> {
  return request<PlayableVersionResponse[]>(`/v1/projects/${encodeURIComponent(projectId)}/playable-versions`)
}

export function playablePreviewUrl(projectId: string, versionId: string): string {
  return `/api/v1/projects/${encodeURIComponent(projectId)}/playable-versions/${encodeURIComponent(versionId)}/preview`
}

export function candidatePreviewUrl(projectId: string, candidateId: string): string {
  return `/api/v1/projects/${encodeURIComponent(projectId)}/candidates/${encodeURIComponent(candidateId)}/preview`
}

export function linkBuildCandidateRepair(parentCandidateId: string, replacementCandidateId: string): Promise<CandidateResponse> {
  return request<CandidateResponse>(`/v1/candidates/${encodeURIComponent(parentCandidateId)}/repair-link`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ replacement_candidate_id: replacementCandidateId }),
  })
}

export function getPublishReview(projectId: string): Promise<PublishReviewResponse> {
  return request<PublishReviewResponse>(`/v1/projects/${encodeURIComponent(projectId)}/publish-review`)
}

export function listProjectReleases(projectId: string): Promise<ReleaseApiResponse[]> {
  return request<ReleaseApiResponse[]>(`/v1/projects/${encodeURIComponent(projectId)}/releases`)
}

export function getProjectRelease(projectId: string, releaseId: string): Promise<ReleaseApiResponse> {
  return request<ReleaseApiResponse>(`/v1/projects/${encodeURIComponent(projectId)}/releases/${encodeURIComponent(releaseId)}`)
}

export function publishProjectRelease(
  projectId: string,
  input: { playableVersionId: string; name: string; description: string },
): Promise<ReleaseApiResponse> {
  return request<ReleaseApiResponse>(`/v1/projects/${encodeURIComponent(projectId)}/releases`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      playable_version_id: input.playableVersionId,
      name: input.name,
      description: input.description,
    }),
  })
}
