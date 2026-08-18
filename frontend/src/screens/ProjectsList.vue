<script setup lang="ts">
import { computed } from 'vue'
import { ArrowRight, FolderOpen, Gamepad2, Lightbulb, Plus } from 'lucide-vue-next'
import type { ProjectResponse } from '../api/client'
import type { ProjectSession } from '../stores/projectStore'
import {
  creationLabel,
  isRecentlyCreated,
  mergeProjectListItems,
  relativeUpdatedLabel,
} from '../contracts/projectListModel.mjs'

const props = defineProps<{
  projects: ProjectSession[]
  remoteProjects?: ProjectResponse[] | null
  projectsLoading?: boolean
  projectListError?: string | null
}>()

const emit = defineEmits<{
  openProject: [projectId: string]
  creator: []
  resources: []
}>()

const stageLabels: Record<string, string> = {
  design_draft: 'Game Design',
  design_review: 'Game Design 待确认',
  gamespec_review: 'GameSpec 待确认',
  ready_to_build: '准备构建',
  building: '正在构建',
  candidate_review: '候选版本待确认',
  playable: '可试玩',
  published: '已发布',
  archived: '已归档',
}

function localStage(project: ProjectSession): string {
  if (project.releases.length > 0) return 'published'
  if (project.playableVersions.length > 0) return 'playable'
  if (project.phase.includes('build') || project.phase.includes('change')) return 'building'
  if (project.designStatus !== 'confirmed') return 'design_draft'
  return 'gamespec_review'
}

const projects = computed(() => mergeProjectListItems(
  props.projects.map((project) => ({
    id: project.id,
    name: project.design.projectTitle,
    createdAt: project.createdAt,
    updatedAt: project.updatedAt,
    stage: localStage(project),
  })),
  props.remoteProjects ?? [],
))

function displayStage(stage: string): string {
  return stageLabels[stage] ?? stage
}
</script>

<template>
  <div class="k01-page projects-page">
    <header class="k01-header">
      <button class="k01-brand" type="button" aria-label="开始创作" @click="emit('creator')">
        <span class="k01-brand-mark"><Gamepad2 :size="18" stroke-width="1.8" /></span>
        <span>AI Cowork Game</span>
      </button>
      <nav class="k01-global-nav" aria-label="全局导航">
        <button class="active" type="button"><FolderOpen :size="16" />Projects</button>
        <button type="button" @click="emit('resources')">我的资源</button>
      </nav>
    </header>

    <main>
      <section v-if="projectsLoading" class="project-list project-list-state" aria-live="polite">
        <span class="project-list-state-kicker">PROJECTS</span>
        <strong>正在加载你的项目…</strong>
      </section>

      <section v-else-if="projectListError" class="project-list project-list-state" role="alert">
        <span class="project-list-state-kicker">PROJECTS</span>
        <strong>{{ projectListError }}</strong>
      </section>

      <section v-else-if="projects.length" class="project-list" aria-labelledby="project-list-title">
        <div class="project-list-heading">
          <div>
            <span>MY PROJECTS</span>
            <h1 id="project-list-title">我的项目</h1>
            <p>继续打开一个项目，或回到创作台开始新的想法。</p>
          </div>
          <div class="project-list-heading-actions">
            <strong>{{ projects.length }}</strong>
            <button class="project-list-create" type="button" @click="emit('creator')"><Plus :size="15" />新建游戏</button>
          </div>
        </div>
        <div class="project-list-items">
          <button v-for="project in projects" :key="project.id" class="project-list-item" type="button" @click="emit('openProject', project.id)">
            <span class="project-list-icon"><Gamepad2 :size="17" /></span>
            <span class="project-list-copy">
              <strong>{{ project.name }}</strong>
              <small class="project-list-meta">
                <em v-if="isRecentlyCreated(project.createdAt)" class="project-list-new">新建</em>
                <span>{{ creationLabel(project.createdAt) }}</span>
                <span aria-hidden="true">·</span>
                <span>{{ relativeUpdatedLabel(project.updatedAt) }}</span>
              </small>
            </span>
            <span class="project-list-stage">{{ displayStage(project.stage) }}</span>
            <ArrowRight :size="16" />
          </button>
        </div>
      </section>

      <section v-else class="project-list project-list-state" aria-live="polite">
        <span class="project-list-state-kicker">MY PROJECTS</span>
        <strong>还没有项目</strong>
        <small>从创作台写下一个想法，开始你的第一个游戏。</small>
        <button class="project-list-create" type="button" @click="emit('creator')"><Lightbulb :size="15" />开始创作</button>
      </section>
    </main>
  </div>
</template>
