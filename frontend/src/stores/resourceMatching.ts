import type { ResourceCandidate } from '../components/resources/resourceTypes'
import type { GameSpecModel, SpecContext } from '../components/workspace/workspaceTypes'

export type ResourceMatch = {
  resourceId: string
  section: SpecContext['key']
  signals: string[]
}

const relationshipFieldValues = (spec: GameSpecModel): string[] => [
  spec.characters.primaryNpcs,
  spec.characters.relationshipGrowth,
  spec.characters.favorRules,
  spec.characters.relationshipEvents,
  spec.characters.requestRewards,
]

function signalHits(signal: string, values: string[]): boolean {
  const normalizedSignal = signal.trim().toLocaleLowerCase()
  return normalizedSignal.length > 0 && values.some((value) => value.toLocaleLowerCase().includes(normalizedSignal))
}

/**
 * Match saved resources against the explicit structured fields they declare.
 * New resource sections must be mapped here rather than falling back to a
 * rendered document or a serialized GameSpec.
 */
export function matchResourcesToSpec(spec: GameSpecModel, resources: ResourceCandidate[]): ResourceMatch[] {
  return resources.flatMap((resource) => {
    const definition = resource.matchSignals
    if (!definition || definition.section !== 'characters') return []

    const signals = definition.signals.filter((signal) => signalHits(signal, relationshipFieldValues(spec)))
    return signals.length >= 2 ? [{ resourceId: resource.id, section: definition.section, signals }] : []
  })
}
