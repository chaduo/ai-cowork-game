import assert from 'node:assert/strict'
import test from 'node:test'

import { readinessForDesignStatus } from '../src/contracts/designReadiness.ts'

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
