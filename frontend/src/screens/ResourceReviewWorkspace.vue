<script setup lang="ts">
import { Gamepad2, PackageCheck } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import CandidateRail from '../components/resources/CandidateRail.vue'
import ResourceDetailReview from '../components/resources/ResourceDetailReview.vue'
import type { ReleaseRecord } from '../components/workspace/releaseTypes'
import {
  extractCandidatesForRelease,
  ignoreCandidate as ignoreCandidateStore,
  saveCandidate as saveCandidateStore,
  undoCandidate as undoCandidateStore,
} from '../stores/projectStore'

const props = defineProps<{ projectId: string; release: ReleaseRecord }>()
const emit = defineEmits<{ back: []; resources: []; projects: [] }>()
const batch = computed(() => extractCandidatesForRelease(props.projectId, props.release.id))
const candidates = computed(() => batch.value.map((item) => item.candidate))
const firstPending = candidates.value.find((candidate) => candidate.status === 'pending')
const selectedId = ref(firstPending?.id ?? candidates.value[0]?.id ?? '')
const selected = computed(() => candidates.value.find((candidate) => candidate.id === selectedId.value) ?? candidates.value[0] ?? null)
const saved = computed(() => candidates.value.filter((candidate) => candidate.status === 'saved').length)
const ignored = computed(() => candidates.value.filter((candidate) => candidate.status === 'ignored').length)
const pending = computed(() => candidates.value.filter((candidate) => candidate.status === 'pending' || candidate.status === 'saving').length)
const processed = computed(() => saved.value + ignored.value)
const complete = computed(() => pending.value === 0)
const hasNextPending = computed(() => candidates.value.some((candidate) => candidate.id !== selectedId.value && candidate.status === 'pending'))
function saveCandidate() {
  if (selected.value) saveCandidateStore(props.projectId, props.release.id, selected.value.id)
}

function ignoreCandidate() {
  if (selected.value) ignoreCandidateStore(props.projectId, props.release.id, selected.value.id)
}

function undoCandidate() {
  if (selected.value) undoCandidateStore(props.projectId, props.release.id, selected.value.id)
}

function selectNextPending() {
  const currentIndex = candidates.value.findIndex((candidate) => candidate.id === selectedId.value)
  const ordered = [...candidates.value.slice(currentIndex + 1), ...candidates.value.slice(0, currentIndex)]
  const next = ordered.find((candidate) => candidate.status === 'pending')
  if (next) selectedId.value = next.id
}

function updateMetadata(payload: { name: string; summary: string }) {
  if (selected.value) Object.assign(selected.value, payload, { cardSummary: payload.summary })
}

function returnToWorkspace() {
  emit('back')
}

function leaveReview(destination: 'resources' | 'projects') {
  if (destination === 'resources') emit('resources')
  else emit('projects')
}
</script>

<template>
  <div class="resource-review-workspace">
    <header class="resource-review-header">
      <div class="workspace-brand"><span><Gamepad2 :size="17" /></span><strong>AI Cowork Game</strong></div>
      <nav class="resource-review-global-nav" aria-label="全局导航"><button type="button" @click="leaveReview('projects')">Projects</button><button type="button" @click="leaveReview('resources')">我的资源</button></nav>
      <div class="workspace-project"><span>PROJECT</span><h1>多代田园物语</h1></div>
      <div class="resource-review-release"><PackageCheck :size="15" /><span><strong>Release v{{ release.version }}</strong><small>基于 Playable v{{ release.basedOnPlayable }}</small></span></div>
    </header>

    <div class="resource-review-layout">
      <CandidateRail v-if="candidates.length" :candidates="candidates" :selected-id="selectedId" :processed="processed" @select="selectedId = $event" @back="returnToWorkspace" />
      <main v-if="selected">
        <div v-if="complete" class="resource-complete-banner"><strong>全部处理完成</strong><span>{{ saved }} 项已保存，{{ ignored }} 项已忽略。你仍然可以选择任意资源撤销决定。</span></div>
        <ResourceDetailReview :candidate="selected" :has-next-pending="hasNextPending" @save="saveCandidate" @ignore="ignoreCandidate" @undo="undoCandidate" @next="selectNextPending" @update-metadata="updateMetadata" />
      </main>
      <main v-else class="resource-gallery-empty"><PackageCheck :size="25" /><h2>没有新的可保存资源</h2><p>这次发布没有发现需要单独保存的新资源。</p></main>
    </div>
  </div>
</template>
