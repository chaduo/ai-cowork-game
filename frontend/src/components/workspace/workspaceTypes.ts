import type { BuildPhase } from './buildTypes'
import type { ChangePhase } from './changeTypes'

export type SpecPhase =
  | 'generating'
  | 'generation_error'
  | 'review'
  | 'revising'
  | 'confirming'
  | 'spec_confirmed'

export type WorkspacePhase = SpecPhase | BuildPhase | ChangePhase

export type ArtifactTab = 'gamespec' | 'build' | 'change' | 'preview' | 'assets' | 'code'

export type SpecContext = {
  key: 'target' | 'gameplay' | 'characters' | 'rules' | 'scope' | 'validation'
  label: string
  path: string[]
}

export type CoworkMessage = {
  id: string
  role: 'ai' | 'user' | 'system'
  text: string
  action?: 'apply-revision'
}

export type PlayableSnapshot = {
  projectTitle: string
  npcNames: string[]
  capabilities: string[]
  previewVariant: 'farm' | 'coffee' | 'generic'
  relationshipSummary: string
}

export type PlayableVersionRecord = {
  version: number
  name: string
  summary: string
  reason: 'initial' | 'change' | 'restore'
  restoredFrom?: number
  basedOnDesign: number
  basedOnSpec: number
  createdAt: number
  snapshot: PlayableSnapshot
}

export type RelationshipDraft = {
  relationshipGrowth: string
  favorRules: string
  relationshipEvents: string
  requestRewards: string
}

export type SourceKind = 'confirmed' | 'default' | 'simplified'

export type GameSpecModel = {
  title: string
  draftLabel: string
  buildTarget: {
    goal: string
    hypothesis: string
  }
  gameplay: {
    coreLoop: string[]
    actions: string[]
  }
  characters: {
    player: string
    playerActions: string[]
    npcName: string
    npcRole: string
    npcBehaviors: string[]
    dialogueStates: string[]
    worldAreas: string[]
    primaryNpcs: string
    relationshipGrowth: string
    favorRules: string
    relationshipEvents: string
    requestRewards: string
  }
  rules: {
    progression: string[]
    completion: string
  }
  scope: {
    included: string[]
    later: string[]
  }
  validation: string[]
  updatedSections: string[]
}
