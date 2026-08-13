<script setup lang="ts">
import { Check, GitCommitHorizontal, History, X } from 'lucide-vue-next'
import type { PlayableVersionRecord } from './workspaceTypes'

const props = defineProps<{ open: boolean; versions: PlayableVersionRecord[]; designVersion: number; specVersion: number }>()
defineEmits<{ close: []; restore: [version: number] }>()
</script>

<template>
  <Transition name="version-drawer">
    <div v-if="open" class="version-history-layer">
      <button class="version-history-scrim" type="button" aria-label="关闭版本历史" @click="$emit('close')"></button>
      <aside class="version-history-drawer" aria-label="版本历史">
        <header><div><span><History :size="13" />版本</span><h2>版本历史</h2><p>只有通过完整验证的版本才会出现在这里。</p></div><button type="button" aria-label="关闭版本历史" @click="$emit('close')"><X :size="16" /></button></header>
        <div class="version-timeline">
          <article v-for="version in [...props.versions].reverse()" :key="version.version" class="version-record" :class="{ 'is-current': version.version === props.versions.at(-1)?.version }">
            <span class="version-marker"><Check :size="13" /></span>
            <div class="version-record-head"><div><span>v{{ version.version }}</span><h3>{{ version.name }}</h3></div><strong>{{ version.version === props.versions.at(-1)?.version ? '当前 · 稳定' : '历史 · 稳定' }}</strong></div>
            <p>{{ version.summary }}</p>
            <ul><li>Playable snapshot · {{ version.reason }}</li><li>Preview · {{ version.snapshot.previewVariant }}</li><li v-if="version.restoredFrom">恢复自 v{{ version.restoredFrom }}</li></ul>
            <footer><span><GitCommitHorizontal :size="12" />基于 Design v{{ version.basedOnDesign }} · GameSpec v{{ version.basedOnSpec }}</span><button v-if="version.version !== props.versions.at(-1)?.version" type="button" @click="$emit('restore', version.version)">恢复此版本</button></footer>
          </article>
        </div>
        <footer class="version-history-note"><Check :size="13" />只有通过验证的 Playable 才会出现在版本历史。当前为 Design v{{ props.designVersion }} · GameSpec v{{ props.specVersion }}。</footer>
      </aside>
    </div>
  </Transition>
</template>
