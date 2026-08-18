import assert from 'node:assert/strict'
import test from 'node:test'

import { mapReleaseResponse, pendingResourceCountFromRelease, releaseDraftFromReview } from '../src/contracts/releaseMapping.ts'

test('maps persisted Release provenance into the Workspace record', () => {
  const release = mapReleaseResponse({
    id: 'release-1',
    project_id: 'project-1',
    playable_version_id: 'playable-2',
    number: 1,
    status: 'published',
    name: '灯塔 · 首个正式版本',
    description: '冻结后的第一版。',
    game_design_revision_id: 'design-rev-3',
    gamespec_revision_id: 'spec-rev-4',
    playable_number: 2,
    game_design_revision_number: 3,
    gamespec_revision_number: 4,
    artifact_path: 'playable/index.html',
    artifact_checksum: 'a'.repeat(64),
    git_commit: 'commit-1',
    published_at: '2026-08-18T02:00:00Z',
    resource_batch: { status: 'empty', candidate_count: 0 },
  })

  assert.deepEqual(release, {
    id: 'release-1',
    version: 1,
    name: '灯塔 · 首个正式版本',
    description: '冻结后的第一版。',
    basedOnPlayable: 2,
    basedOnGameDesign: 3,
    basedOnGameSpec: 4,
    status: 'published',
    createdAt: '2026-08-18T02:00:00.000Z',
    playableVersionId: 'playable-2',
    gameDesignRevisionId: 'design-rev-3',
    gamespecRevisionId: 'spec-rev-4',
    artifactPath: 'playable/index.html',
    artifactChecksum: 'a'.repeat(64),
    gitCommit: 'commit-1',
    resourceBatchStatus: 'empty',
    resourceCandidateCount: 0,
  })
})

test('does not invent pending resource count for an empty batch', () => {
  assert.equal(
    pendingResourceCountFromRelease({ status: 'published', resource_batch: { status: 'empty', candidate_count: 0 } }),
    0,
  )
})

test('builds a local Publish Review draft from persisted remote provenance', () => {
  assert.deepEqual(
    releaseDraftFromReview({
      next_release_number: 2,
      playable_number: 3,
      game_design_revision_number: 4,
      gamespec_revision_number: 5,
    }, '灯塔', '完成核心目标'),
    {
      version: 2,
      name: '灯塔 · Release 2',
      description: '完成核心目标',
      basedOnPlayable: 3,
      basedOnGameDesign: 4,
      basedOnGameSpec: 5,
    },
  )
})
