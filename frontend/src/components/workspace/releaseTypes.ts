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
}

export type ReleaseDraft = Omit<ReleaseRecord, 'id' | 'status' | 'createdAt'>
