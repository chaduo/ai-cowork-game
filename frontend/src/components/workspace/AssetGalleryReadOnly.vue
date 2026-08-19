<script setup lang="ts">
import { FileImage, Headphones, ImageOff, LockKeyhole, RefreshCw, Type, X } from 'lucide-vue-next'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ApiClientError, listPlayableAssets, type PlayableAssetResponse } from '../../api/client'
import { formatAssetSize, groupPlayableAssets } from '../../contracts/playableAssets'

const props = defineProps<{
  projectId: string | null
  versionId: string | null
  projectTitle: string
}>()

const assets = ref<PlayableAssetResponse[]>([])
const gitCommit = ref('')
const loading = ref(false)
const error = ref<string | null>(null)
const selectedImage = ref<PlayableAssetResponse | null>(null)
const failedImages = ref(new Set<string>())
let requestToken = 0

const groups = computed(() => groupPlayableAssets(assets.value))
const assetCount = computed(() => assets.value.length)

async function loadAssets() {
  const token = ++requestToken
  selectedImage.value = null
  failedImages.value = new Set()
  error.value = null
  assets.value = []
  gitCommit.value = ''
  if (!props.projectId || !props.versionId) {
    loading.value = false
    return
  }
  loading.value = true
  try {
    const response = await listPlayableAssets(props.projectId, props.versionId)
    if (token !== requestToken) return
    assets.value = response.assets
    gitCommit.value = response.git_commit
  } catch (cause) {
    if (token !== requestToken) return
    error.value = cause instanceof ApiClientError ? cause.message : '无法读取当前 Playable 的资源。'
  } finally {
    if (token === requestToken) loading.value = false
  }
}

function markImageFailed(path: string) {
  failedImages.value = new Set([...failedImages.value, path])
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') selectedImage.value = null
}

watch(() => [props.projectId, props.versionId], loadAssets, { immediate: true })
onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => {
  requestToken += 1
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <article class="asset-gallery-readonly">
    <header>
      <div>
        <span><FileImage :size="12" />ASSETS · PLAYABLE</span>
        <h1>{{ projectTitle }} · Assets</h1>
        <p v-if="gitCommit">{{ assetCount }} files · {{ gitCommit.slice(0, 10) }}</p>
        <p v-else>当前 Playable</p>
      </div>
      <span><LockKeyhole :size="13" />Read only</span>
    </header>

    <section v-if="!projectId || !versionId" class="asset-state-panel">
      <ImageOff :size="24" />
      <strong>还没有 Playable</strong>
      <p>完成平台验证、人工试玩确认并 Promote 后，资源会显示在这里。</p>
    </section>

    <section v-else-if="loading" class="asset-loading" aria-label="正在读取 Playable 资源">
      <div v-for="index in 8" :key="index"><span></span><i></i><i></i></div>
    </section>

    <section v-else-if="error" class="asset-state-panel is-error" role="alert">
      <ImageOff :size="24" />
      <strong>资源读取失败</strong>
      <p>{{ error }}</p>
      <button type="button" @click="loadAssets"><RefreshCw :size="14" />重新读取</button>
    </section>

    <section v-else-if="assetCount === 0" class="asset-state-panel">
      <ImageOff :size="24" />
      <strong>这个版本没有独立资源文件</strong>
      <p>当前画面可能由 Canvas 或代码直接绘制。</p>
    </section>

    <template v-else>
      <section v-if="groups.images.length" class="asset-file-section">
        <div class="asset-section-heading"><span><FileImage :size="14" /></span><div><h2>Images</h2><small>{{ groups.images.length }} files</small></div></div>
        <div class="asset-grid">
          <button v-for="asset in groups.images" :key="asset.path" type="button" class="asset-tile" @click="selectedImage = asset">
            <span class="asset-image-frame">
              <img v-if="!failedImages.has(asset.path)" :src="asset.content_url" :alt="asset.name" loading="lazy" @error="markImageFailed(asset.path)" />
              <span v-else class="asset-image-failed"><ImageOff :size="22" /><small>Unavailable</small></span>
            </span>
            <span class="asset-file-copy"><strong>{{ asset.name }}</strong><small>{{ asset.mime_type }} · {{ formatAssetSize(asset.size_bytes) }}</small><em>{{ asset.path }}</em></span>
          </button>
        </div>
      </section>

      <section v-if="groups.audio.length" class="asset-file-section">
        <div class="asset-section-heading"><span><Headphones :size="14" /></span><div><h2>Audio</h2><small>{{ groups.audio.length }} files</small></div></div>
        <div class="audio-assets">
          <article v-for="asset in groups.audio" :key="asset.path">
            <div><Headphones :size="15" /><span><strong>{{ asset.name }}</strong><small>{{ formatAssetSize(asset.size_bytes) }} · {{ asset.path }}</small></span></div>
            <audio controls preload="metadata" :src="asset.content_url"></audio>
          </article>
        </div>
      </section>

      <section v-if="groups.fonts.length" class="asset-file-section">
        <div class="asset-section-heading"><span><Type :size="14" /></span><div><h2>Fonts</h2><small>{{ groups.fonts.length }} files</small></div></div>
        <div class="font-assets">
          <article v-for="asset in groups.fonts" :key="asset.path">
            <span>Aa</span><div><strong>{{ asset.name }}</strong><small>{{ asset.mime_type }} · {{ formatAssetSize(asset.size_bytes) }}</small><em>{{ asset.path }}</em></div>
          </article>
        </div>
      </section>
    </template>

    <div v-if="selectedImage" class="asset-preview-backdrop" role="presentation" @click.self="selectedImage = null">
      <section class="asset-preview-dialog" role="dialog" aria-modal="true" :aria-label="selectedImage.name">
        <header><div><strong>{{ selectedImage.name }}</strong><small>{{ selectedImage.mime_type }} · {{ formatAssetSize(selectedImage.size_bytes) }} · {{ selectedImage.path }}</small></div><button type="button" title="关闭预览" @click="selectedImage = null"><X :size="18" /></button></header>
        <div><img :src="selectedImage.content_url" :alt="selectedImage.name" /></div>
      </section>
    </div>
  </article>
</template>
