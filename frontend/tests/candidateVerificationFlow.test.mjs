import assert from 'node:assert/strict'
import test from 'node:test'

import {
  buildCandidateRepairRequest,
  nextCandidateVerificationAction,
  runCandidateVerificationFlow,
} from '../src/contracts/candidateVerificationFlow.ts'

const idle = {
  testRunning: false,
  repairRunning: false,
  hasTransportError: false,
}

test('automatically verifies an untested candidate', () => {
  assert.equal(nextCandidateVerificationAction({
    ...idle,
    testGateStatus: 'untested',
    hasReport: false,
    repairRound: 0,
  }), 'verify')
})

test('stops automatic work at human review after pass', () => {
  assert.equal(nextCandidateVerificationAction({
    ...idle,
    testGateStatus: 'ready',
    hasReport: true,
    repairRound: 1,
  }), 'human_review')
})

test('repairs persisted failed and invalid reports below the limit', () => {
  for (const testGateStatus of ['failed', 'invalid']) {
    assert.equal(nextCandidateVerificationAction({
      ...idle,
      testGateStatus,
      hasReport: true,
      repairRound: 2,
    }), 'repair')
  }
})

test('stops after three repair rounds', () => {
  assert.equal(nextCandidateVerificationAction({
    ...idle,
    testGateStatus: 'failed',
    hasReport: true,
    repairRound: 3,
  }), 'stopped')
})

test('requires manual retry after a transport failure without a report', () => {
  assert.equal(nextCandidateVerificationAction({
    ...idle,
    testGateStatus: 'untested',
    hasReport: false,
    repairRound: 0,
    hasTransportError: true,
  }), 'manual_retry')
})

test('waits while verification or repair is already running', () => {
  for (const running of [
    { testRunning: true, repairRunning: false },
    { testRunning: false, repairRunning: true },
  ]) {
    assert.equal(nextCandidateVerificationAction({
      ...idle,
      ...running,
      testGateStatus: 'untested',
      hasReport: false,
      repairRound: 0,
    }), 'wait')
  }
})

test('builds a bounded repair request from persisted failure evidence', () => {
  const request = buildCandidateRepairRequest({
    repairRound: 1,
    summary: 'Core gameplay acceptance failed',
    diagnostics: [{ code: 'movement_stuck', message: 'Player did not move' }],
    evidence: [
      { kind: 'core_input', status: 'failed', observed: 'x remained 0' },
      { kind: 'console', status: 'passed', observed: 'no errors' },
    ],
  })

  assert.match(request, /Repair round 2 of 3/)
  assert.match(request, /Core gameplay acceptance failed/)
  assert.match(request, /core_input: x remained 0/)
  assert.doesNotMatch(request, /console: no errors/)
  assert.match(request, /movement_stuck: Player did not move/)
  assert.ok(request.length <= 4000)
})

test('truncates oversized repair context to the API request limit', () => {
  const request = buildCandidateRepairRequest({
    repairRound: 0,
    summary: 'x'.repeat(5000),
    diagnostics: [],
    evidence: [],
  })

  assert.equal(request.length, 4000)
})

test('runs verify repair verify and stops at human review', async () => {
  const calls = []
  let state = {
    candidateId: 'candidate-1',
    testGateStatus: 'untested',
    testReport: null,
    repairRound: 0,
    testRunning: false,
    repairRunning: false,
    testError: null,
  }

  await runCandidateVerificationFlow({
    getState: () => state,
    verify: async () => {
      calls.push(`verify:${state.candidateId}`)
      if (state.candidateId === 'candidate-1') {
        state = {
          ...state,
          testGateStatus: 'failed',
          testReport: { summary: 'movement failed', diagnostics: [], evidence: [] },
        }
      } else {
        state = { ...state, testGateStatus: 'ready', testReport: { summary: 'passed', diagnostics: [], evidence: [] } }
      }
      return true
    },
    repair: async (request) => {
      calls.push(`repair:${request.includes('movement failed')}`)
      state = {
        candidateId: 'candidate-2',
        testGateStatus: 'untested',
        testReport: null,
        repairRound: 1,
        testRunning: false,
        repairRunning: false,
        testError: null,
      }
      return true
    },
  })

  assert.deepEqual(calls, ['verify:candidate-1', 'repair:true', 'verify:candidate-2'])
  assert.equal(state.testGateStatus, 'ready')
})

test('does not repair a candidate at the automatic repair limit', async () => {
  let repairCalls = 0
  await runCandidateVerificationFlow({
    getState: () => ({
      candidateId: 'candidate-4',
      testGateStatus: 'failed',
      testReport: { summary: 'still failing', diagnostics: [], evidence: [] },
      repairRound: 3,
      testRunning: false,
      repairRunning: false,
      testError: null,
    }),
    verify: async () => true,
    repair: async () => {
      repairCalls += 1
      return true
    },
  })

  assert.equal(repairCalls, 0)
})

test('stops orchestration when verification transport fails', async () => {
  let verifyCalls = 0
  await runCandidateVerificationFlow({
    getState: () => ({
      candidateId: 'candidate-1',
      testGateStatus: 'untested',
      testReport: null,
      repairRound: 0,
      testRunning: false,
      repairRunning: false,
      testError: verifyCalls ? 'Chrome unavailable' : null,
    }),
    verify: async () => {
      verifyCalls += 1
      return false
    },
    repair: async () => true,
  })

  assert.equal(verifyCalls, 1)
})
