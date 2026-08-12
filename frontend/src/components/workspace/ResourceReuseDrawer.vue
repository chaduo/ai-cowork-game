<script setup lang="ts">
import { Check, Heart, X } from 'lucide-vue-next'
import ResourcePreview from '../resources/ResourcePreview.vue'
import type { ResourceCandidate } from '../resources/resourceTypes'

defineProps<{ open: boolean; resource: ResourceCandidate; used: boolean }>()
defineEmits<{ close: []; use: [] }>()
</script>

<template>
  <Transition name="resource-reuse-drawer">
    <div v-if="open" class="resource-reuse-layer">
      <button class="resource-reuse-scrim" type="button" aria-label="关闭资源详情" @click="$emit('close')"></button>
      <aside class="resource-reuse-drawer" aria-label="资源详情">
        <header><div class="reuse-drawer-title"><span><Heart :size="18" /></span><div><h2>{{ resource.name }}</h2><p>玩法模块 · 来自「{{ resource.provenance.projectName }}」</p></div></div><button type="button" aria-label="关闭资源详情" @click="$emit('close')"><X :size="17" /></button></header>
        <div class="resource-reuse-drawer-body">
          <section><h3>这是什么</h3><p>{{ resource.summary }}</p></section>
          <section class="reuse-fit-section"><h3>为什么适合当前设计</h3><p>当前「咖啡店故事」也需要通过 NPC 委托和日常互动积累关系，并在关键节点触发人物事件。这个资源可以提供通用关系结构，同时继续使用 Emily、Alex 和咖啡店的当前语境。</p></section>
          <ResourcePreview :candidate="resource" compact title="在原游戏中的表现" />
          <section><h3>包含内容</h3><div class="reuse-included-list"><p v-for="item in ['NPC 委托规则', '好感成长规则', '关系事件触发']" :key="item"><Check :size="14" />{{ item }}</p></div></section>
          <section><h3>以后可以调整</h3><div class="reuse-config-list"><div v-for="field in resource.configurableFields" :key="field.name"><strong>{{ field.name }}</strong><span>{{ field.description }}</span></div></div></section>
          <section><h3>来源</h3><div class="resource-provenance"><strong>{{ resource.provenance.projectName }}</strong><span>{{ resource.provenance.releaseVersion }}</span><span>{{ resource.provenance.playableVersion }}</span></div></section>
        </div>
        <footer><button type="button" @click="$emit('close')">关闭</button><button type="button" class="primary" :disabled="used" @click="$emit('use')">{{ used ? '已使用' : '使用这个资源' }}</button></footer>
      </aside>
    </div>
  </Transition>
</template>
