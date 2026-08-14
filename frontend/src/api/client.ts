import type { CreatorGameDesignDraft } from '../contracts/creatorGameDesign'
import type { CreatorGameSpec } from '../contracts/creatorGameSpec'

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
  status: 'draft' | 'submitted' | 'confirmed'
  confirmed_at: string | null
  draft: CreatorGameDesignDraft
}

export interface GameSpecResponse {
  project_id: string
  revision_id: string
  revision_number: number
  status: 'draft' | 'confirmed' | 'superseded'
  confirmed_at: string | null
  validation_errors: Array<Record<string, unknown>>
  spec: CreatorGameSpec
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
