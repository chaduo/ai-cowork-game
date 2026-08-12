<script setup lang="ts">
import { Heart } from 'lucide-vue-next'
import type { ResourceCandidate } from './resourceTypes'

withDefaults(defineProps<{ candidate: ResourceCandidate; compact?: boolean; title?: string }>(), { compact: false, title: '' })
</script>

<template>
  <section class="resource-preview" :class="[`is-${candidate.type}`, { 'is-compact': compact }]">
    <h2>{{ title || (candidate.type === 'gameplay' ? '当前游戏中的表现' : '资源预览') }}</h2>

    <div v-if="candidate.type === 'gameplay'" class="gameplay-evidence-grid">
      <figure>
        <div class="gameplay-shot is-request"><img src="/farm-game-preview.png" alt="当前游戏中 Lucy 提出委托的场景" /><div class="scene-dialogue"><strong>Lucy 的委托</strong><span>今天可以帮我送一篮草莓吗？</span></div></div>
        <figcaption><strong>NPC 委托</strong><span>角色提出任务，玩家选择是否接受。</span></figcaption>
      </figure>
      <figure>
        <div class="gameplay-shot is-favor"><img src="/farm-game-preview.png" alt="当前游戏中完成互动后好感增加的场景" /><div class="scene-favor"><Heart :size="18" fill="currentColor" /><strong>好感 +5</strong><i><span></span></i></div></div>
        <figcaption><strong>好感变化</strong><span>完成互动后，玩家立即看到关系成长。</span></figcaption>
      </figure>
      <figure>
        <div class="gameplay-shot is-event"><img src="/farm-game-preview.png" alt="当前游戏中关系事件解锁的场景" /><div class="scene-event"><strong>新的关系事件</strong><span>Lucy 邀请你一起参加春日庆典。</span></div></div>
        <figcaption><strong>关系事件</strong><span>达到条件后，解锁新的角色互动。</span></figcaption>
      </figure>
    </div>

    <div v-else-if="candidate.type === 'ui'" class="ui-resource-preview">
      <img src="/farm-game-preview.png" alt="好感心形 UI 在当前游戏画面中的实际表现" />
      <div class="favor-ui-sample">
        <div><span class="favor-avatar">露</span><span><strong>Lucy</strong><small>关系状态 · 亲近</small></span><em>好感 +5</em></div>
        <div class="favor-ui-hearts"><Heart v-for="index in 5" :key="index" :size="26" :fill="index <= 3 ? 'currentColor' : 'none'" /></div>
        <div class="favor-ui-progress"><i><span></span></i><strong>60 / 100</strong></div>
      </div>
    </div>

    <div v-else class="visual-assets-grid">
      <figure><div class="asset-thumb"><div class="rural-panel-sample"><strong>收获完成</strong><small>小麦 × 12</small></div></div><figcaption>木质面板</figcaption></figure>
      <figure><div class="asset-thumb"><button type="button">确认</button></div><figcaption>按钮样式</figcaption></figure>
      <figure><div class="asset-thumb"><div class="rural-toolbar-sample"><span>锄</span><span>种</span><span>浇</span></div></div><figcaption>工具栏</figcaption></figure>
      <figure><div class="asset-thumb"><div class="rural-dialogue-sample"><strong>Lucy</strong><p>今年的收成看起来很好。</p></div></div><figcaption>对话框</figcaption></figure>
      <figure><div class="asset-thumb"><div class="rural-inventory-sample"><i v-for="index in 6" :key="index"></i></div></div><figcaption>背包格子</figcaption></figure>
      <figure><div class="asset-thumb"><div class="rural-status-sample"><Heart :size="13" fill="currentColor" /><i><span></span></i></div></div><figcaption>状态条</figcaption></figure>
    </div>
  </section>
</template>
