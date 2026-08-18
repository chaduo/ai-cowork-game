import test from 'node:test'
import assert from 'node:assert/strict'
import {
  creationLabel,
  mergeProjectListItems,
  relativeUpdatedLabel,
} from '../src/contracts/projectListModel.mjs'

test('remote project timestamps stay authoritative over a newly hydrated local session', () => {
  const items = mergeProjectListItems(
    [{ id: 'p1', name: '竞技场守卫', createdAt: 1_700_000_000_000, updatedAt: 1_800_000_000_000 }],
    [{ id: 'p1', name: '竞技场守卫', created_at: '2026-08-18T10:00:00Z', updated_at: '2026-08-18T10:07:00Z', stage: 'design_draft' }],
  )

  assert.equal(items[0].updatedAt, Date.parse('2026-08-18T10:07:00Z'))
  assert.equal(items[0].createdAt, Date.parse('2026-08-18T10:00:00Z'))
})

test('project list labels creation separately from the last update', () => {
  const now = Date.parse('2026-08-18T12:00:00Z')

  const expectedTime = new Date(Date.parse('2026-08-18T11:52:00Z')).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
  assert.equal(creationLabel(Date.parse('2026-08-18T11:52:00Z'), now), `刚创建 · ${expectedTime}`)
  assert.equal(relativeUpdatedLabel(Date.parse('2026-08-18T11:30:00Z'), now), '30 分钟前更新')
})

test('sorts the most recently updated project first regardless of API input order', () => {
  const items = mergeProjectListItems([], [
    { id: 'older', name: '旧项目', created_at: '2026-08-18T09:00:00Z', updated_at: '2026-08-18T09:10:00Z', stage: 'playable' },
    { id: 'published', name: '刚发布', created_at: '2026-08-18T08:00:00Z', updated_at: '2026-08-18T11:55:00Z', stage: 'published' },
  ])

  assert.deepEqual(items.map((item) => item.id), ['published', 'older'])
})
