<script setup lang="ts">
import { ArrowLeft, BadgeCheck, Gamepad2, PackageCheck, Play, X } from 'lucide-vue-next'
import type { ReleaseRecord } from './releaseTypes'

defineProps<{ open: boolean; release: ReleaseRecord | null }>()
defineEmits<{ close: []; play: [] }>()
</script>

<template>
  <Transition name="version-drawer">
    <div v-if="open && release" class="release-detail-layer">
      <button class="release-detail-scrim" type="button" aria-label="返回 Workspace" @click="$emit('close')"></button>
      <aside class="release-detail-drawer" aria-label="Release 详情">
        <header>
          <div><span><PackageCheck :size="13" />RELEASE</span><h2>Release v{{ release.version }}</h2><p>这个正式版本已经冻结。</p></div>
          <button type="button" aria-label="关闭 Release 详情" @click="$emit('close')"><X :size="17" /></button>
        </header>
        <div class="release-detail-content">
          <div class="release-detail-title"><small>当前正式版本</small><h3>{{ release.name }}</h3><strong><BadgeCheck :size="13" />已发布</strong></div>
          <div class="release-detail-preview"><img src="/farm-game-preview.png" alt="Release v1 游戏预览" /><span><PackageCheck :size="14" />RELEASE v{{ release.version }}</span></div>
          <section><span>版本说明</span><p>{{ release.description }}</p></section>
          <section class="release-source-grid"><span>来源记录</span><p><Gamepad2 :size="14" /><strong>Playable v{{ release.basedOnPlayable }}</strong></p><p>GameSpec v{{ release.basedOnGameSpec }}</p><p>Game Design v{{ release.basedOnGameDesign }}</p></section>
          <section><span>Validation</span><p class="release-pass"><BadgeCheck :size="14" /><strong>Passed</strong> · 发布时验证证据已记录</p></section>
          <section><span>发布于</span><p>{{ release.createdAt }}</p></section>
        </div>
        <footer><button type="button" @click="$emit('close')"><ArrowLeft :size="14" />返回 Workspace</button><button class="primary" type="button" @click="$emit('play')"><Play :size="14" />试玩此 Release</button></footer>
      </aside>
    </div>
  </Transition>
</template>
