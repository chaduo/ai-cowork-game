<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import K01CreateProject from './screens/K01CreateProject.vue'
import K02ProjectWorkspace from './screens/K02ProjectWorkspace.vue'
import MyResources from './screens/MyResources.vue'
import ResourceReviewWorkspace from './screens/ResourceReviewWorkspace.vue'
import type { ConfirmedGameDesign } from './components/kickoff/kickoffTypes'
import type { ReleaseRecord } from './components/workspace/releaseTypes'
import { appendPlayableVersion, completeGeneration, configureDemoRuntime, createProject, getActiveProject, getPendingResourceCount, openProject, projectStore, setProjectDesignStatus, startGeneration, updateSavedResourceMetadata } from './stores/projectStore'
import { seedDemo, type AppSurface } from './stores/demoSeeds'
import { getProjectDesign, getProjectRecord, listProjectRecords, type ProjectResponse } from './api/client'

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
const projectRecords = ref<ProjectResponse[] | null>(requestedScreen ? null : [])
const projectsLoading = ref(!requestedScreen)
const projectListError = ref<string | null>(null)
const designResumeProjectId = ref<string | null>(null)

function designFromRecord(record: ProjectResponse): ConfirmedGameDesign {
  return {
    originalIdea: record.original_idea,
    projectTitle: record.name,
    scenarioId: 'generic',
    summary: {
      title: record.name,
      summary: record.original_idea,
      highlights: [],
      coreLoop: [],
    },
    decisions: [],
  }
}

function upsertProjectRecord(record: ProjectResponse): void {
  if (!projectRecords.value) projectRecords.value = []
  const index = projectRecords.value.findIndex((item) => item.id === record.id)
  if (index === -1) projectRecords.value.push(record)
  else projectRecords.value[index] = record
}

function hydrateProjectSession(record: ProjectResponse) {
  const existing = projectStore.projects.find((project) => project.id === record.id)
  const session = existing ?? createProject(designFromRecord(record), record.id)
  if (existing) openProject(record.id)
  // A restored local session already contains the prototype's durable build
  // state. Only new sessions need the initial local generation transition.
  if (!existing) completeGeneration(session.id)
  if (record.current_playable && session.playableVersions.length === 0) {
    appendPlayableVersion(session.id, {
      reason: 'initial',
      name: `${record.name} · Playable v${record.current_playable.number}`,
      summary: '从已保存的 Project 状态恢复。',
    })
  }
  if (record.latest_release && session.releases.length === 0) {
    session.releases.push({
      id: record.latest_release.id,
      version: record.latest_release.number,
      name: `${record.name} · Release ${record.latest_release.number}`,
      description: '从已保存的 Project 状态恢复。',
      basedOnPlayable: record.current_playable?.number ?? 0,
      basedOnGameDesign: session.designVersion,
      basedOnGameSpec: session.specVersion,
      status: 'published',
      createdAt: new Date(record.updated_at).toLocaleDateString('zh-CN'),
    })
  }
  return session
}

onMounted(async () => {
  if (requestedScreen) return
  projectsLoading.value = true
  try {
    const records = await listProjectRecords()
    projectRecords.value = records
    for (const record of records) {
      hydrateProjectSession(record)
    }
    projectStore.activeProjectId = null
  } catch {
    projectListError.value = '暂时无法加载项目列表，请确认后端已启动。'
    projectRecords.value = []
  } finally {
    projectsLoading.value = false
  }
})

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

async function enterWorkspace(design: ConfirmedGameDesign, projectId: string) {
  try {
    const record = await getProjectRecord(projectId)
    upsertProjectRecord(record)
  } catch {
    projectListError.value = '项目已经创建，但暂时无法读取项目状态。'
  }
  const session = createProject(design, projectId)
  setProjectDesignStatus(session.id, 'confirmed')
  startGeneration(session.id)
  surface.value = 'workspace'
}

async function openWorkspace(projectId: string) {
  try {
    const designResponse = await getProjectDesign(projectId)
    if (designResponse.status !== 'confirmed') {
      designResumeProjectId.value = projectId
      surface.value = 'projects'
      return
    }
  } catch (cause) {
    if (!(cause instanceof Error && 'code' in cause && (cause as { code?: string }).code === 'project_not_found')) {
      // Offline demo/local sessions can still be opened from the in-memory store.
    }
  }
  if (!openProject(projectId)) {
    try {
      const record = await getProjectRecord(projectId)
      upsertProjectRecord(record)
      hydrateProjectSession(record)
    } catch {
      projectListError.value = '找不到这个项目，可能已经被移除或暂时不可用。'
      return
    }
  }
  surface.value = 'workspace'
}
</script>

<template>
  <MyResources v-if="surface === 'resources'" @projects="surface = 'projects'" @update-metadata="updateSavedMetadata" />
  <ResourceReviewWorkspace v-else-if="surface === 'review' && reviewedRelease && activeProject" :project-id="activeProject.id" :project-name="activeProject.spec.title" :release="reviewedRelease" @back="closeResourceReview()" @resources="closeResourceReview('resources')" @projects="closeResourceReview('projects')" />
  <K02ProjectWorkspace v-else-if="surface === 'workspace' && activeProject" :key="activeProject.id" :design="activeProject.design" :resource-pending-count="pendingResourceCount" @back="surface = 'projects'" @resources="surface = 'resources'" @review-resources="openResourceReview" />
  <K01CreateProject v-else :projects="projectStore.projects" :remote-projects="projectRecords" :resume-project-id="designResumeProjectId" :projects-loading="projectsLoading" :project-list-error="projectListError" @open-project="openWorkspace" @enter-workspace="enterWorkspace" @resume-consumed="designResumeProjectId = null" @resources="surface = 'resources'" />
</template>
