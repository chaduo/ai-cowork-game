import type { DesignReadiness } from './creatorGameDesign'

export type DesignClarificationStatus = 'clarifying' | 'ready' | 'iterating' | 'confirmed'
export type DesignDraftPhase = DesignClarificationStatus | 'thinking' | 'iterating-question' | 'confirming' | 'error'

export function clarificationStatusForPhase(phase: DesignDraftPhase): DesignClarificationStatus {
  if (phase === 'ready' || phase === 'confirming' || phase === 'confirmed') return 'ready'
  if (phase === 'iterating' || phase === 'iterating-question') return 'iterating'
  return 'clarifying'
}

export function readinessForDesignStatus(status: DesignClarificationStatus): DesignReadiness {
  const isReady = status === 'ready' || status === 'confirmed'
  return {
    status: isReady ? 'ready' : 'not_ready',
    blockers: [],
    unresolved_decisions: [],
    checked_at: null,
  }
}
