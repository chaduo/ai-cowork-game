import assert from 'node:assert/strict'
import test from 'node:test'

import { createGameSpecFixture } from '../src/components/workspace/gameSpecFixture.ts'
import { creatorGameSpecFromViewModel } from '../src/contracts/creatorGameSpecMapping.ts'

test('generic design with an empty provider core loop still produces a saveable GameSpec', () => {
  const design = {
    originalIdea: '一个小守卫在竞技场中抵抗机械敌人。',
    projectTitle: '机械竞技场',
    scenarioId: 'generic',
    summary: {
      title: '机械竞技场',
      summary: '通过走位和近战攻击抵抗敌人。',
      highlights: ['生存紧张感'],
      coreLoop: [],
      progression: [],
    },
    decisions: [],
  }

  const payload = creatorGameSpecFromViewModel(createGameSpecFixture(design))

  assert.ok(payload.gameplay.core_loop.length > 0)
  assert.ok(payload.gameplay.core_loop.every((step) => step.trim().length > 0))
})

test('saving an existing session repairs an empty core loop at the API boundary', () => {
  const model = createGameSpecFixture({
    originalIdea: '一个小守卫在竞技场中抵抗机械敌人。',
    projectTitle: '机械竞技场',
    scenarioId: 'generic',
    summary: {
      title: '机械竞技场',
      summary: '通过走位和近战攻击抵抗敌人。',
      highlights: ['生存紧张感'],
      coreLoop: ['移动', '攻击', '结算'],
    },
    decisions: [],
  })
  model.gameplay.coreLoop = []

  const payload = creatorGameSpecFromViewModel(model)

  assert.ok(payload.gameplay.core_loop.length > 0)
})
