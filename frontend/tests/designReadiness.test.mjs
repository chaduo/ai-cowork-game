import assert from 'node:assert/strict'
import test from 'node:test'

import { clarificationStatusForPhase, readinessForDesignStatus } from '../src/contracts/designReadiness.ts'

test('ready design phase produces a confirmable readiness contract', () => {
  assert.deepEqual(readinessForDesignStatus('ready'), {
    status: 'ready',
    blockers: [],
    unresolved_decisions: [],
    checked_at: null,
  })
})

test('clarifying design phase remains blocked from confirmation', () => {
  assert.deepEqual(readinessForDesignStatus('clarifying'), {
    status: 'not_ready',
    blockers: [],
    unresolved_decisions: [],
    checked_at: null,
  })
})

test('confirming phase keeps the ready contract while the API request is in flight', () => {
  assert.equal(clarificationStatusForPhase('confirming'), 'ready')
})
