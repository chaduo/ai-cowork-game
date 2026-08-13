<script setup lang="ts">
import { Boxes, FolderOpen, Gamepad2, Search, X } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import ResourceGalleryCard from '../components/resources/ResourceGalleryCard.vue'
import SavedResourceDetail from '../components/resources/SavedResourceDetail.vue'
import type { ResourceCandidate, ResourceCandidateType } from '../components/resources/resourceTypes'
import { projectStore } from '../stores/projectStore'

const emit = defineEmits<{ projects: []; updateMetadata: [payload: { id: string; name: string; summary: string }] }>()
type ResourceFilter = 'all' | ResourceCandidateType

const query = ref('')
const filter = ref<ResourceFilter>('all')
const selectedId = ref<string | null>(null)
const resources = computed(() => projectStore.savedResources)
const selected = computed(() => resources.value.find((resource) => resource.id === selectedId.value) ?? null)
const filters: { id: ResourceFilter; label: string }[] = [
  { id: 'all', label: '全部' }, { id: 'gameplay', label: '玩法' }, { id: 'ui', label: 'UI' }, { id: 'visual', label: '美术' },
]
const filteredResources = computed(() => {
  const normalized = query.value.trim().toLocaleLowerCase()
  return resources.value.filter((resource) => {
    if (filter.value !== 'all' && resource.type !== filter.value) return false
    if (!normalized) return true
    return [resource.name, resource.summary, resource.cardSummary, resource.provenance.projectName]
      .join(' ').toLocaleLowerCase().includes(normalized)
  })
})
const hasSavedResources = computed(() => resources.value.length > 0)
</script>

<template>
  <div class="my-resources-page">
    <header class="global-creator-header">
      <div class="global-creator-brand"><span><Gamepad2 :size="17" /></span><strong>AI Cowork Game</strong></div>
      <nav aria-label="全局导航"><button type="button" @click="$emit('projects')"><FolderOpen :size="15" />Projects</button><button type="button" class="active"><Boxes :size="15" />我的资源</button></nav>
    </header>

    <SavedResourceDetail v-if="selected" :resource="selected" @back="selectedId = null" @update-metadata="$emit('updateMetadata', $event)" />

    <main v-else class="my-resources-gallery">
      <header><h1>我的资源</h1><p>你在创作过程中保存的内容，可以在其他游戏中继续使用。</p></header>
      <section class="resource-gallery-controls" aria-label="筛选资源">
        <label class="resource-search"><Search :size="16" /><input v-model="query" type="search" placeholder="搜索资源" aria-label="搜索资源" /><button v-if="query" type="button" aria-label="清空搜索" @click="query = ''"><X :size="14" /></button></label>
        <div class="resource-filter-tabs" role="group" aria-label="资源分类"><button v-for="item in filters" :key="item.id" type="button" :class="{ active: filter === item.id }" @click="filter = item.id">{{ item.label }}</button></div>
      </section>
      <p v-if="hasSavedResources" class="resource-result-count">{{ filteredResources.length }} 项资源</p>
      <section v-if="filteredResources.length" class="saved-resource-grid" aria-label="已保存资源">
        <ResourceGalleryCard v-for="resource in filteredResources" :key="resource.id" :resource="resource" @open="selectedId = $event" />
      </section>
      <section v-else class="resource-gallery-empty"><Boxes :size="25" /><h2>{{ hasSavedResources ? '没有找到匹配的资源' : '还没有保存的资源' }}</h2><p>{{ hasSavedResources ? '换一个关键词，或者查看其他分类。' : '完成发布后，可以把值得复用的内容保存到这里。' }}</p></section>
    </main>
  </div>
</template>
