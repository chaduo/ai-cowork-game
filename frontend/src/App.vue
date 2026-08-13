<script setup lang="ts">
import { computed, ref } from 'vue'
import BuildPlayScreen from './screens/BuildPlayScreen.vue'
import K01CreateProject from './screens/K01CreateProject.vue'
import K02ProjectWorkspace from './screens/K02ProjectWorkspace.vue'
import MyResources from './screens/MyResources.vue'
import ResourceReviewWorkspace from './screens/ResourceReviewWorkspace.vue'
import { createDemoConfirmedDesign, createResourceReuseConfirmedDesign } from './components/workspace/gameSpecFixture'
import type { ConfirmedGameDesign } from './components/kickoff/kickoffTypes'
import type { ReleaseRecord } from './components/workspace/releaseTypes'
import { getActiveProject, getPendingResourceCount, projectStore, updateSavedResourceMetadata } from './stores/projectStore'

const screen = new URLSearchParams(window.location.search).get('screen')
type AppSurface = 'projects' | 'workspace' | 'resources' | 'review'
const surface = ref<AppSurface>(screen === 'my-resources' ? 'resources' : screen === 'resources' ? 'review' : screen === 'gamespec' || screen === 'resource-reuse' || screen === 'build' || screen === 'change' || screen === 'publish' ? 'workspace' : 'projects')
const workspaceDesign = ref<ConfirmedGameDesign | null>(screen === 'resource-reuse' ? createResourceReuseConfirmedDesign() : screen === 'gamespec' || screen === 'build' || screen === 'change' || screen === 'publish' || screen === 'resources' ? createDemoConfirmedDesign() : null)
const resourceReleaseFixture: ReleaseRecord = { id: 'release-v1', version: 1, name: '多代田园物语 · First Release', description: '完成核心经营、NPC 关系与代际传承体验的第一个正式版本。', basedOnPlayable: 2, basedOnGameDesign: 2, basedOnGameSpec: 2, status: 'published', createdAt: '刚刚' }
const reviewedRelease = ref<ReleaseRecord | null>(screen === 'resources' ? resourceReleaseFixture : null)
const activeProject = computed(() => getActiveProject())
const savedResources = computed(() => projectStore.savedResources)
const pendingResourceCount = computed(() => activeProject.value ? getPendingResourceCount(activeProject.value) : 0)
const relationshipResource = computed(() => savedResources.value.find((resource) => resource.id === 'relationship-system') ?? null)

function openResourceReview(release: ReleaseRecord) {
  reviewedRelease.value = release
  surface.value = 'review'
}

function closeResourceReview(destination: AppSurface = 'workspace') {
  surface.value = destination
}

function updateSavedMetadata(payload: { id: string; name: string; summary: string }) {
  updateSavedResourceMetadata(payload.id, payload)
}

function enterWorkspace(design: ConfirmedGameDesign) {
  workspaceDesign.value = design
  surface.value = 'workspace'
}
</script>

<template>
  <BuildPlayScreen v-if="screen === 'build-play'" />
  <MyResources v-else-if="surface === 'resources'" :resources="savedResources" @projects="surface = 'projects'" @update-metadata="updateSavedMetadata" />
  <ResourceReviewWorkspace v-else-if="surface === 'review' && reviewedRelease && activeProject" :project-id="activeProject.id" :release="reviewedRelease" @back="closeResourceReview()" @resources="closeResourceReview('resources')" @projects="closeResourceReview('projects')" />
  <K02ProjectWorkspace v-else-if="surface === 'workspace' && workspaceDesign" :design="workspaceDesign" :initial-release="reviewedRelease" :resource-pending-count="pendingResourceCount" :relationship-resource="relationshipResource" @back="surface = 'projects'" @resources="surface = 'resources'" @review-resources="openResourceReview" />
  <K01CreateProject v-else @enter-workspace="enterWorkspace" @resources="surface = 'resources'" />
</template>
