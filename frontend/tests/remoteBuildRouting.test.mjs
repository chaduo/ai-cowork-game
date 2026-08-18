import assert from 'node:assert/strict'
import test from 'node:test'

import { routeRemoteBuildState } from '../src/contracts/remoteBuildRouting.ts'

test('keeps an existing playable while a newer build is running', () => {
  assert.equal(routeRemoteBuildState({ status: 'running', candidateId: null, playableCandidateId: 'old-candidate' }), 'building')
})

test('shows an unpromoted candidate even when an older playable exists', () => {
  assert.equal(routeRemoteBuildState({ status: 'succeeded', candidateId: 'new-candidate', playableCandidateId: 'old-candidate' }), 'candidate')
})

test('returns to playable after the candidate that was promoted becomes current', () => {
  assert.equal(routeRemoteBuildState({ status: 'succeeded', candidateId: 'new-candidate', playableCandidateId: 'new-candidate' }), 'playable')
})

test('keeps the old playable visible while a later build fails', () => {
  assert.equal(routeRemoteBuildState({ status: 'failed', candidateId: null, playableCandidateId: 'old-candidate' }), 'error')
})

test('treats a succeeded build without a candidate as invalid output', () => {
  assert.equal(routeRemoteBuildState({ status: 'succeeded', candidateId: null, playableCandidateId: null }), 'error')
})
