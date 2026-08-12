<script setup lang="ts">
import { Gamepad2, PackageCheck } from 'lucide-vue-next'
import { computed, onBeforeUnmount, ref } from 'vue'
import CandidateRail from '../components/resources/CandidateRail.vue'
import ResourceDetailReview from '../components/resources/ResourceDetailReview.vue'
import type { ResourceCandidate } from '../components/resources/resourceTypes'
import type { ReleaseRecord } from '../components/workspace/releaseTypes'

const props = defineProps<{ release: ReleaseRecord; initialCandidates: ResourceCandidate[] }>()
const emit = defineEmits<{ back: [candidates: ResourceCandidate[]]; resources: [candidates: ResourceCandidate[]]; projects: [candidates: ResourceCandidate[]] }>()
const candidates = ref<ResourceCandidate[]>(props.initialCandidates.map(cloneCandidate))
const firstPending = candidates.value.find((candidate) => candidate.status === 'pending')
const selectedId = ref(firstPending?.id ?? candidates.value[0]!.id)
const selected = computed(() => candidates.value.find((candidate) => candidate.id === selectedId.value) ?? candidates.value[0]!)
const saved = computed(() => candidates.value.filter((candidate) => candidate.status === 'saved').length)
const ignored = computed(() => candidates.value.filter((candidate) => candidate.status === 'ignored').length)
const pending = computed(() => candidates.value.filter((candidate) => candidate.status === 'pending' || candidate.status === 'saving').length)
const processed = computed(() => saved.value + ignored.value)
const complete = computed(() => pending.value === 0)
const hasNextPending = computed(() => candidates.value.some((candidate) => candidate.id !== selectedId.value && candidate.status === 'pending'))
let saveTimer: number | null = null

function cloneCandidate(candidate: ResourceCandidate): ResourceCandidate {
  return { ...candidate, configurableFields: candidate.configurableFields.map((field) => ({ ...field })) }
}

function saveCandidate() {
  if (selected.value.status !== 'pending') return
  const id = selected.value.id
  selected.value.status = 'saving'
  if (saveTimer !== null) window.clearTimeout(saveTimer)
  saveTimer = window.setTimeout(() => {
    const candidate = candidates.value.find((item) => item.id === id)
    if (candidate) candidate.status = 'saved'
  }, 420)
}

function ignoreCandidate() {
  if (selected.value.status === 'pending') selected.value.status = 'ignored'
}

function undoCandidate() {
  if (selected.value.status === 'saved' || selected.value.status === 'ignored') selected.value.status = 'pending'
}

function selectNextPending() {
  const currentIndex = candidates.value.findIndex((candidate) => candidate.id === selectedId.value)
  const ordered = [...candidates.value.slice(currentIndex + 1), ...candidates.value.slice(0, currentIndex)]
  const next = ordered.find((candidate) => candidate.status === 'pending')
  if (next) selectedId.value = next.id
}

function updateMetadata(payload: { name: string; summary: string }) {
  selected.value.name = payload.name
  selected.value.summary = payload.summary
  selected.value.cardSummary = payload.summary
}

function returnToWorkspace() {
  emit('back', candidates.value.map(cloneCandidate))
}

function leaveReview(destination: 'resources' | 'projects') {
  const snapshot = candidates.value.map(cloneCandidate)
  if (destination === 'resources') emit('resources', snapshot)
  else emit('projects', snapshot)
}

onBeforeUnmount(() => { if (saveTimer !== null) window.clearTimeout(saveTimer) })
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
      <CandidateRail :candidates="candidates" :selected-id="selectedId" :processed="processed" @select="selectedId = $event" @back="returnToWorkspace" />
      <main>
        <div v-if="complete" class="resource-complete-banner"><strong>全部处理完成</strong><span>{{ saved }} 项已保存，{{ ignored }} 项已忽略。你仍然可以选择任意资源撤销决定。</span></div>
        <ResourceDetailReview :candidate="selected" :has-next-pending="hasNextPending" @save="saveCandidate" @ignore="ignoreCandidate" @undo="undoCandidate" @next="selectNextPending" @update-metadata="updateMetadata" />
      </main>
    </div>
  </div>
</template>
