import assert from 'node:assert/strict'
import test from 'node:test'

import { previewUrlForPhase } from '../src/contracts/previewRouting.ts'

test('uses the candidate preview only while the candidate is awaiting review', () => {
  assert.equal(
    previewUrlForPhase('candidate_ready', '/candidate-preview', '/playable-preview'),
    '/candidate-preview',
  )
})

test('uses the promoted playable preview after promotion', () => {
  assert.equal(
    previewUrlForPhase('playable_ready', '/candidate-preview', '/playable-preview'),
    '/playable-preview',
  )
})
