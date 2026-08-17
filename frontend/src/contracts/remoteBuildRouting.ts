export type RemoteBuildRoute = 'building' | 'candidate' | 'playable' | 'error'

export type RemoteBuildRoutingInput = {
  status: string
  candidateId?: string | null
  playableCandidateId?: string | null
}

/**
 * Resolve the durable server state before choosing a Workspace surface.
 * A current Playable is not evidence that a newer Candidate disappeared;
 * compare candidate ids so a later build can remain in its Human Gate.
 */
export function routeRemoteBuildState(input: RemoteBuildRoutingInput): RemoteBuildRoute {
  if (input.status === 'succeeded' && input.candidateId) {
    return input.playableCandidateId === input.candidateId ? 'playable' : 'candidate'
  }
  if (input.status === 'succeeded') return 'error'
  if (['failed', 'cancelled', 'timed_out', 'invalid_output', 'unsupported'].includes(input.status)) return 'error'
  return 'building'
}
