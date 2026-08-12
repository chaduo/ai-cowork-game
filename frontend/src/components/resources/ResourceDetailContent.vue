<script setup lang="ts">
import { Check, Heart, Image, LayoutPanelTop, Minus } from 'lucide-vue-next'
import ResourcePreview from './ResourcePreview.vue'
import type { ResourceCandidate } from './resourceTypes'

withDefaults(defineProps<{ resource: ResourceCandidate; mode?: 'review' | 'saved' }>(), { mode: 'saved' })
</script>

<template>
  <article class="resource-detail-review" :class="{ 'is-saved-detail': mode === 'saved' }">
    <header>
      <div class="resource-detail-icon"><Heart v-if="resource.type === 'gameplay'" :size="22" /><LayoutPanelTop v-else-if="resource.type === 'ui'" :size="22" /><Image v-else :size="22" /></div>
      <div>
        <h1>{{ resource.name }}</h1>
        <div class="resource-detail-tags"><span class="candidate-tag">{{ resource.type === 'gameplay' ? '玩法模块' : resource.type === 'ui' ? 'UI 模块' : '美术资源' }}</span><span v-if="mode === 'review'" class="candidate-tag" :class="resource.status === 'saved' ? 'is-good' : resource.status === 'ignored' ? 'is-muted' : 'is-warn'">{{ resource.status === 'saved' ? '已保存' : resource.status === 'ignored' ? '已忽略' : resource.status === 'saving' ? '正在保存' : '待确认' }}</span></div>
        <p v-if="mode === 'saved'" class="saved-resource-summary">{{ resource.summary }}</p>
      </div>
    </header>

    <section class="resource-copy-section"><h2>这是什么</h2><p class="resource-definition">{{ resource.summary }}</p></section>
    <section class="resource-copy-section"><h2>为什么 AI 认为它值得复用</h2><p class="resource-ai-reason">{{ resource.reuseReason }}</p></section>
    <ResourcePreview :candidate="resource" />

    <section class="resource-copy-section">
      <h2 v-if="mode === 'saved'" class="resource-content-heading">资源内容</h2>
      <div class="resource-boundary-grid"><div><h2>{{ mode === 'saved' ? '包含内容' : '会一起保存' }}</h2><p v-for="item in resource.included" :key="item"><Check :size="14" />{{ item }}</p></div><div><h2>{{ mode === 'saved' ? '不包含' : '不会一起保存' }}</h2><p v-for="item in resource.excluded" :key="item"><Minus :size="14" />{{ item }}</p></div></div>
    </section>

    <section class="resource-copy-section"><h2>以后可以调整</h2><div class="resource-config-grid"><div v-for="field in resource.configurableFields" :key="field.name"><strong>{{ field.name }}</strong><span>{{ field.description }}</span></div></div></section>
    <section class="resource-copy-section"><h2>来源</h2><div class="resource-provenance"><strong>{{ resource.provenance.projectName }}</strong><span>{{ resource.provenance.releaseVersion }}</span><span>{{ resource.provenance.playableVersion }}</span><span>{{ resource.provenance.gameSpecVersion }}</span></div></section>
  </article>
</template>
