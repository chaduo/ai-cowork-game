import type { ReleaseRecord } from '../components/workspace/releaseTypes'
import type { ReleaseDraft } from '../components/workspace/releaseTypes'

export type ResourceBatchApiResponse = {
  status: string
  candidate_count: number
}

export type ReleaseApiResponse = {
  id: string
  project_id: string
  playable_version_id: string
  number: number
  status: 'published' | string
  name: string
  description: string
  game_design_revision_id: string | null
  gamespec_revision_id: string | null
  playable_number?: number | null
  game_design_revision_number?: number | null
  gamespec_revision_number?: number | null
  artifact_path: string | null
  artifact_checksum: string | null
  git_commit: string | null
  published_at: string
  resource_batch: ResourceBatchApiResponse
}

export function mapReleaseResponse(record: ReleaseApiResponse): ReleaseRecord {
  return {
    id: record.id,
    version: record.number,
    name: record.name,
    description: record.description,
    basedOnPlayable: record.playable_number ?? 0,
    basedOnGameDesign: record.game_design_revision_number ?? 0,
    basedOnGameSpec: record.gamespec_revision_number ?? 0,
    status: 'published',
    createdAt: new Date(record.published_at).toISOString(),
    playableVersionId: record.playable_version_id,
    gameDesignRevisionId: record.game_design_revision_id,
    gamespecRevisionId: record.gamespec_revision_id,
    artifactPath: record.artifact_path,
    artifactChecksum: record.artifact_checksum,
    gitCommit: record.git_commit,
    resourceBatchStatus: record.resource_batch.status,
    resourceCandidateCount: record.resource_batch.candidate_count,
  }
}

export function pendingResourceCountFromRelease(record: Pick<ReleaseApiResponse, 'status' | 'resource_batch'>): number {
  if (record.status !== 'published') return 0
  if (!['ready', 'pending'].includes(record.resource_batch.status)) return 0
  return Math.max(0, record.resource_batch.candidate_count)
}

export function releaseDraftFromReview(
  review: {
    next_release_number: number
    playable_number: number | null
    game_design_revision_number?: number | null
    gamespec_revision_number?: number | null
  },
  projectTitle: string,
  fallbackDescription: string,
): ReleaseDraft {
  return {
    version: review.next_release_number,
    name: `${projectTitle} · Release ${review.next_release_number}`,
    description: fallbackDescription,
    basedOnPlayable: review.playable_number ?? 0,
    basedOnGameDesign: review.game_design_revision_number ?? 0,
    basedOnGameSpec: review.gamespec_revision_number ?? 0,
  }
}
