<script setup lang="ts">
import { Eye, Heart, Sparkles, X } from 'lucide-vue-next'
import type { ResourceCandidate } from '../resources/resourceTypes'

defineProps<{ resource: ResourceCandidate }>()
defineEmits<{ view: []; use: []; dismiss: [] }>()
</script>

<template>
  <aside class="resource-reuse-recommendation">
    <header><span><Sparkles :size="14" />发现一个可能适合的已有资源</span><button type="button" aria-label="忽略推荐" title="忽略推荐" @click="$emit('dismiss')"><X :size="15" /></button></header>
    <div class="reuse-recommendation-resource"><span><Heart :size="19" /></span><div><strong>{{ resource.name }}</strong><small>来自「{{ resource.provenance.projectName }}」</small></div></div>
    <div class="reuse-match-reason"><strong>为什么推荐</strong><p>当前 GameSpec 同样需要 NPC 委托、好感成长和关系事件，这个资源已经实现了相近的关系成长方式。</p></div>
    <footer><button type="button" @click="$emit('view')"><Eye :size="14" />查看资源</button><button type="button" class="primary" @click="$emit('use')">使用这个资源</button></footer>
    <p class="reuse-draft-note">资源复用只影响当前 GameSpec Draft，不会立即开始 Build。</p>
  </aside>
</template>
