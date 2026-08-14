export type RecoveryPhase = 'generating' | 'generation_error' | string
export type GameSpecPersistenceStatus = 'missing' | 'draft' | 'confirmed' | 'superseded' | string

export function shouldResumeGameSpecGeneration(
  phase: RecoveryPhase,
  gamespecStatus: GameSpecPersistenceStatus,
): boolean {
  return gamespecStatus === 'missing' && (phase === 'generating' || phase === 'generation_error')
}
