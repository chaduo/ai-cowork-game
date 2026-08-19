import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

import { formatAssetSize, groupPlayableAssets } from '../src/contracts/playableAssets.ts'


const assets = [
  {
    path: 'assets/hero.png',
    name: 'hero.png',
    kind: 'image',
    mime_type: 'image/png',
    size_bytes: 1024,
    content_url: '/api/v1/content?path=assets%2Fhero.png',
  },
  {
    path: 'audio/theme.ogg',
    name: 'theme.ogg',
    kind: 'audio',
    mime_type: 'audio/ogg',
    size_bytes: 1536,
    content_url: '/api/v1/content?path=audio%2Ftheme.ogg',
  },
  {
    path: 'fonts/game.woff2',
    name: 'game.woff2',
    kind: 'font',
    mime_type: 'font/woff2',
    size_bytes: 0,
    content_url: '/api/v1/content?path=fonts%2Fgame.woff2',
  },
]


test('groups immutable playable assets without rewriting encoded content URLs', () => {
  const grouped = groupPlayableAssets(assets)

  assert.deepEqual(grouped.images.map((asset) => asset.name), ['hero.png'])
  assert.deepEqual(grouped.audio.map((asset) => asset.name), ['theme.ogg'])
  assert.deepEqual(grouped.fonts.map((asset) => asset.name), ['game.woff2'])
  assert.equal(grouped.images[0].content_url.includes('%2F'), true)
})


test('formats asset byte sizes for compact file metadata', () => {
  assert.equal(formatAssetSize(0), '0 B')
  assert.equal(formatAssetSize(1023), '1023 B')
  assert.equal(formatAssetSize(1024), '1 KB')
  assert.equal(formatAssetSize(1536), '1.5 KB')
  assert.equal(formatAssetSize(1024 * 1024), '1 MB')
})


test('asset workspace renders server images and contains no mock preview dependency', async () => {
  const source = await readFile(new URL('../src/components/workspace/AssetGalleryReadOnly.vue', import.meta.url), 'utf8')

  assert.match(source, /<img[^>]+:src="asset\.content_url"/)
  assert.doesNotMatch(source, /farm-game-preview\.png/)
  assert.doesNotMatch(source, /Mock asset/)
})
