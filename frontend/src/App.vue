<script setup lang="ts">
import { computed, ref } from 'vue'
import K01CreateProject from './screens/K01CreateProject.vue'
import K02ProjectWorkspace from './screens/K02ProjectWorkspace.vue'
import MyResources from './screens/MyResources.vue'
import ResourceReviewWorkspace from './screens/ResourceReviewWorkspace.vue'
import type { ConfirmedGameDesign } from './components/kickoff/kickoffTypes'
import type { ReleaseRecord } from './components/workspace/releaseTypes'
import { createProject, getActiveProject, getPendingResourceCount, openProject, projectStore, updateSavedResourceMetadata } from './stores/projectStore'

type AppSurface = 'projects' | 'workspace' | 'resources' | 'review'
const surface = ref<AppSurface>('projects')
const reviewedRelease = ref<ReleaseRecord | null>(null)
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
  <ResourceReviewWorkspace v-else-if="surface === 'review' && reviewedRelease && activeProject" :project-id="activeProject.id" :release="reviewedRelease" @back="closeResourceReview()" @resources="closeResourceReview('resources')" @projects="closeResourceReview('projects')" />
  <K02ProjectWorkspace v-else-if="surface === 'workspace' && activeProject" :key="activeProject.id" :design="activeProject.design" :initial-release="reviewedRelease" :resource-pending-count="pendingResourceCount" @back="surface = 'projects'" @resources="surface = 'resources'" @review-resources="openResourceReview" />
  <K01CreateProject v-else :projects="projectStore.projects" @open-project="openWorkspace" @enter-workspace="enterWorkspace" @resources="surface = 'resources'" />
</template>
