<script setup lang="ts">
import { Heart } from 'lucide-vue-next'
import type { ResourceCandidate } from './resourceTypes'

defineProps<{ resource: ResourceCandidate }>()
defineEmits<{ open: [id: string] }>()
</script>

<template>
  <button class="saved-resource-card" type="button" @click="$emit('open', resource.id)">
    <span class="saved-card-preview" :class="`is-${resource.type}`">
      <span v-if="resource.type === 'gameplay'" class="saved-game-preview">
        <img src="/farm-game-preview.png" alt="NPC 关系系统在多代田园物语中的游戏表现" />
        <span class="saved-game-dialogue"><strong>Lucy 的委托</strong><small>可以帮我送一篮草莓吗？</small></span>
        <span class="saved-game-favor"><Heart :size="13" fill="currentColor" />好感 +5</span>
      </span>
      <span v-else-if="resource.type === 'ui'" class="saved-ui-preview">
        <img src="/farm-game-preview.png" alt="好感心形 UI 本体" />
        <span class="saved-ui-panel"><span><strong>Lucy</strong><small>好感 +5</small></span><span class="saved-ui-hearts">♥ ♥ ♥ ♡ ♡</span><i><span></span></i><em>60 / 100</em></span>
      </span>
      <span v-else class="saved-visual-preview">
        <span class="saved-asset-cell"><i class="saved-wood-panel"></i></span>
        <span class="saved-asset-cell"><b>确认</b></span>
        <span class="saved-asset-cell"><i class="saved-toolbar"><b></b><b></b><b></b></i></span>
        <span class="saved-asset-cell"><i class="saved-dialogue">今年的收成真不错！</i></span>
      </span>
    </span>
    <span class="saved-card-body">
      <span class="saved-type-label">{{ resource.type === 'gameplay' ? '玩法模块' : resource.type === 'ui' ? 'UI 模块' : '美术资源' }}</span>
      <strong>{{ resource.name }}</strong>
      <span class="saved-card-summary">{{ resource.cardSummary }}</span>
      <span class="saved-card-source">来自「{{ resource.provenance.projectName }}」</span>
    </span>
  </button>
</template>
