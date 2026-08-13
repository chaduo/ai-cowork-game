<script setup lang="ts">
import { computed, ref } from 'vue'
import K01CreateProject from './screens/K01CreateProject.vue'
import K02ProjectWorkspace from './screens/K02ProjectWorkspace.vue'
import MyResources from './screens/MyResources.vue'
import ResourceReviewWorkspace from './screens/ResourceReviewWorkspace.vue'
import type { ConfirmedGameDesign } from './components/kickoff/kickoffTypes'
import type { ReleaseRecord } from './components/workspace/releaseTypes'
import { configureDemoRuntime, createProject, getActiveProject, getPendingResourceCount, openProject, projectStore, updateSavedResourceMetadata } from './stores/projectStore'
import { seedDemo, type AppSurface } from './stores/demoSeeds'

function parseDemoFlags(search: string) {
  const params = new URLSearchParams(search)
  return {
    specError: params.get('specError') === '1',
    buildError: params.get('buildError') === '1',
    scopeError: params.get('scopeError') === '1',
    publishError: params.get('publishError') === '1',
    kickoffError: params.get('kickoffError') === '1',
  }
}

const requestedScreen = new URLSearchParams(window.location.search).get('screen')
const demoNames = new Set<Parameters<typeof seedDemo>[0]>(['gamespec', 'build', 'change', 'publish', 'resource-reuse', 'resources', 'my-resources'])
const demoFlags = parseDemoFlags(window.location.search)
if (!requestedScreen) configureDemoRuntime(demoFlags)
const initialSurface = requestedScreen && demoNames.has(requestedScreen as Parameters<typeof seedDemo>[0])
  ? seedDemo(requestedScreen as Parameters<typeof seedDemo>[0], demoFlags)
  : 'projects'
const surface = ref<AppSurface>(initialSurface)
const reviewedRelease = ref<ReleaseRecord | null>(initialSurface === 'review' ? getActiveProject()?.releases.at(-1) ?? null : null)
const activeProject = computed(() => getActiveProject())
const pendingResourceCount = computed(() => activeProject.value ? getPendingResourceCount(activeProject.value) : 0)

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
  createProject(design)
  surface.value = 'workspace'
}

function openWorkspace(projectId: string) {
  if (!openProject(projectId)) return
  surface.value = 'workspace'
}
</script>

<template>
  <MyResources v-if="surface === 'resources'" @projects="surface = 'projects'" @update-metadata="updateSavedMetadata" />
  <ResourceReviewWorkspace v-else-if="surface === 'review' && reviewedRelease && activeProject" :project-id="activeProject.id" :project-name="activeProject.spec.title" :release="reviewedRelease" @back="closeResourceReview()" @resources="closeResourceReview('resources')" @projects="closeResourceReview('projects')" />
  <K02ProjectWorkspace v-else-if="surface === 'workspace' && activeProject" :key="activeProject.id" :design="activeProject.design" :resource-pending-count="pendingResourceCount" @back="surface = 'projects'" @resources="surface = 'resources'" @review-resources="openResourceReview" />
  <K01CreateProject v-else :projects="projectStore.projects" @open-project="openWorkspace" @enter-workspace="enterWorkspace" @resources="surface = 'resources'" />
</template>
