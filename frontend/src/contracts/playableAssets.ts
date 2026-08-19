import type { PlayableAssetResponse } from '../api/client'

export type PlayableAssetGroups = {
  images: PlayableAssetResponse[]
  audio: PlayableAssetResponse[]
  fonts: PlayableAssetResponse[]
}

export function groupPlayableAssets(assets: PlayableAssetResponse[]): PlayableAssetGroups {
  return {
    images: assets.filter((asset) => asset.kind === 'image'),
    audio: assets.filter((asset) => asset.kind === 'audio'),
    fonts: assets.filter((asset) => asset.kind === 'font'),
  }
}

export function formatAssetSize(sizeBytes: number): string {
  if (sizeBytes < 1024) return `${sizeBytes} B`
  const kilobytes = sizeBytes / 1024
  if (kilobytes < 1024) return `${Number(kilobytes.toFixed(1))} KB`
  return `${Number((kilobytes / 1024).toFixed(1))} MB`
}
