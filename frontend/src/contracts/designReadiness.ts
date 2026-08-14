import type { DesignReadiness } from './creatorGameDesign'

export type DesignClarificationStatus = 'clarifying' | 'ready' | 'iterating' | 'confirmed'

export function readinessForDesignStatus(status: DesignClarificationStatus): DesignReadiness {
  const isReady = status === 'ready' || status === 'confirmed'
  return {
    status: isReady ? 'ready' : 'not_ready',
    blockers: [],
    unresolved_decisions: [],
    checked_at: null,
  }
}
