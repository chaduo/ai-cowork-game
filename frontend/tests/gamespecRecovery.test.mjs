import assert from 'node:assert/strict'
import test from 'node:test'

import { shouldResumeGameSpecGeneration } from '../src/contracts/gamespecRecovery.ts'

test('missing GameSpec resumes an interrupted generation phase', () => {
  assert.equal(shouldResumeGameSpecGeneration('generating', 'missing'), true)
})

test('a completed or persisted GameSpec does not restart generation', () => {
  assert.equal(shouldResumeGameSpecGeneration('review', 'missing'), false)
  assert.equal(shouldResumeGameSpecGeneration('generating', 'draft'), false)
  assert.equal(shouldResumeGameSpecGeneration('playable_ready', 'confirmed'), false)
})
