export type ReleasePhase = 'review' | 'publishing' | 'error' | 'success'

export type ReleaseRecord = {
  id: string
  version: number
  name: string
  description: string
  basedOnPlayable: number
  basedOnGameDesign: number
  basedOnGameSpec: number
  status: 'published'
  createdAt: string
  playableVersionId?: string
  gameDesignRevisionId?: string | null
  gamespecRevisionId?: string | null
  artifactPath?: string | null
  artifactChecksum?: string | null
  gitCommit?: string | null
  resourceBatchStatus?: string
  resourceCandidateCount?: number
}

export type ReleaseDraft = Omit<ReleaseRecord, 'id' | 'status' | 'createdAt'>
