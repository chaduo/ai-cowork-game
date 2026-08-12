<script setup lang="ts">
import { computed, ref } from 'vue'
import BuildPlayScreen from './screens/BuildPlayScreen.vue'
import K01CreateProject from './screens/K01CreateProject.vue'
import K02ProjectWorkspace from './screens/K02ProjectWorkspace.vue'
import MyResources from './screens/MyResources.vue'
import ResourceReviewWorkspace from './screens/ResourceReviewWorkspace.vue'
import { createDemoConfirmedDesign, createResourceReuseConfirmedDesign } from './components/workspace/gameSpecFixture'
import { createResourceCandidates, createSavedResources } from './components/resources/resourceFixtures'
import type { ConfirmedGameDesign } from './components/kickoff/kickoffTypes'
import type { ResourceCandidate } from './components/resources/resourceTypes'
import type { ReleaseRecord } from './components/workspace/releaseTypes'

const screen = new URLSearchParams(window.location.search).get('screen')
type AppSurface = 'projects' | 'workspace' | 'resources' | 'review'
const surface = ref<AppSurface>(screen === 'my-resources' ? 'resources' : screen === 'resources' ? 'review' : screen === 'gamespec' || screen === 'resource-reuse' || screen === 'build' || screen === 'change' || screen === 'publish' ? 'workspace' : 'projects')
const workspaceDesign = ref<ConfirmedGameDesign | null>(screen === 'resource-reuse' ? createResourceReuseConfirmedDesign() : screen === 'gamespec' || screen === 'build' || screen === 'change' || screen === 'publish' || screen === 'resources' ? createDemoConfirmedDesign() : null)
const resourceReleaseFixture: ReleaseRecord = { id: 'release-v1', version: 1, name: '多代田园物语 · First Release', description: '完成核心经营、NPC 关系与代际传承体验的第一个正式版本。', basedOnPlayable: 2, basedOnGameDesign: 2, basedOnGameSpec: 2, status: 'published', createdAt: '刚刚' }
const reviewedRelease = ref<ReleaseRecord | null>(screen === 'resources' ? resourceReleaseFixture : null)
const resourceCandidates = ref<ResourceCandidate[]>(createResourceCandidates())
const savedResources = ref<ResourceCandidate[]>(createSavedResources())
const pendingResourceCount = ref(resourceCandidates.value.filter((candidate) => candidate.status === 'pending').length)
const relationshipResource = computed(() => savedResources.value.find((resource) => resource.id === 'relationship-system') ?? null)

function openResourceReview(release: ReleaseRecord) {
  reviewedRelease.value = release
  surface.value = 'review'
}

function closeResourceReview(candidates: ResourceCandidate[], destination: AppSurface = 'workspace') {
  resourceCandidates.value = candidates
  pendingResourceCount.value = candidates.filter((candidate) => candidate.status === 'pending').length
  for (const candidate of candidates.filter((item) => item.status === 'saved')) upsertSavedResource(candidate)
  surface.value = destination
}

function cloneResource(resource: ResourceCandidate): ResourceCandidate {
  return { ...resource, configurableFields: resource.configurableFields.map((field) => ({ ...field })) }
}

function upsertSavedResource(resource: ResourceCandidate) {
  const index = savedResources.value.findIndex((item) => item.id === resource.id)
  const saved = { ...cloneResource(resource), status: 'saved' as const }
  if (index === -1) savedResources.value.push(saved)
  else savedResources.value[index] = saved
}

function updateSavedMetadata(payload: { id: string; name: string; summary: string }) {
  const saved = savedResources.value.find((resource) => resource.id === payload.id)
  if (saved) Object.assign(saved, { name: payload.name, summary: payload.summary, cardSummary: payload.summary })
  const candidate = resourceCandidates.value.find((resource) => resource.id === payload.id)
  if (candidate) Object.assign(candidate, { name: payload.name, summary: payload.summary })
}

function enterWorkspace(design: ConfirmedGameDesign) {
  workspaceDesign.value = design
  surface.value = 'workspace'
}
</script>

<template>
  <BuildPlayScreen v-if="screen === 'build-play'" />
  <MyResources v-else-if="surface === 'resources'" :resources="savedResources" @projects="surface = 'projects'" @update-metadata="updateSavedMetadata" />
  <ResourceReviewWorkspace v-else-if="surface === 'review' && reviewedRelease" :release="reviewedRelease" :initial-candidates="resourceCandidates" @back="closeResourceReview" @resources="closeResourceReview($event, 'resources')" @projects="closeResourceReview($event, 'projects')" />
  <K02ProjectWorkspace v-else-if="surface === 'workspace' && workspaceDesign" :design="workspaceDesign" :initial-release="reviewedRelease" :resource-pending-count="pendingResourceCount" :relationship-resource="relationshipResource" @back="surface = 'projects'" @resources="surface = 'resources'" @review-resources="openResourceReview" />
  <K01CreateProject v-else @enter-workspace="enterWorkspace" @resources="surface = 'resources'" />
</template>
