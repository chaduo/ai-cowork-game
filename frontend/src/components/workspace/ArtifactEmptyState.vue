<script setup lang="ts">
import { Check, Circle, Code2, Image, MonitorPlay } from 'lucide-vue-next'
import type { ArtifactTab } from './workspaceTypes'

defineProps<{ tab: Exclude<ArtifactTab, 'gamespec' | 'build' | 'change'> }>()

const copy = {
  preview: { icon: MonitorPlay, eyebrow: 'NO PLAYABLE VERSION YET', title: '还没有可试玩版本', body: '确认 GameSpec 后，Cowork AI 会开始构建第一个 Working Build。' },
  assets: { icon: Image, eyebrow: 'ASSETS · NOT STARTED', title: '素材会在 Build 阶段出现', body: '角色、NPC、道具和场景素材会跟随 First Playable Scope 生成。' },
  code: { icon: Code2, eyebrow: 'CODE · NOT STARTED', title: '代码会在 Build 阶段出现', body: '确认规格后，AI 才会基于固定 Phaser 模板开始开发。' },
}
</script>

<template>
  <section class="artifact-empty">
    <component :is="copy[tab].icon" :size="28" />
    <span>{{ copy[tab].eyebrow }}</span>
    <h2>{{ copy[tab].title }}</h2>
    <p>{{ copy[tab].body }}</p>
    <div class="empty-lifecycle"><span><Check :size="12" />Game Design</span><i></i><span class="current"><Circle :size="10" />GameSpec</span><i></i><span><Circle :size="10" />Build</span></div>
  </section>
</template>
