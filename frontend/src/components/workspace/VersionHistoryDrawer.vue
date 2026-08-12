<script setup lang="ts">
import { Check, GitCommitHorizontal, History, X } from 'lucide-vue-next'

defineProps<{ open: boolean }>()
defineEmits<{ close: [] }>()
</script>

<template>
  <Transition name="version-drawer">
    <div v-if="open" class="version-history-layer">
      <button class="version-history-scrim" type="button" aria-label="关闭版本历史" @click="$emit('close')"></button>
      <aside class="version-history-drawer" aria-label="版本历史">
        <header><div><span><History :size="13" />版本</span><h2>版本历史</h2><p>只有通过完整验证的版本才会出现在这里。</p></div><button type="button" aria-label="关闭版本历史" @click="$emit('close')"><X :size="16" /></button></header>
        <div class="version-timeline">
          <article class="version-record is-current">
            <span class="version-marker"><Check :size="13" /></span>
            <div class="version-record-head"><div><span>v2</span><h3>NPC 关系反馈增强</h3></div><strong>当前 · 稳定</strong></div>
            <p>Favor 30 触发关系事件，并增加会随 Favor 更新的心形好感条。</p>
            <ul><li>玩法规则 · 更新</li><li>关系 HUD · 新增</li><li>角色与场景素材 · 复用</li></ul>
            <footer><span><GitCommitHorizontal :size="12" />基于 Design v2 · GameSpec v2</span><strong>6 / 6 PASS</strong></footer>
          </article>
          <article class="version-record">
            <span class="version-marker"><Check :size="13" /></span>
            <div class="version-record-head"><div><span>v1</span><h3>初始可玩版本</h3></div><strong>历史 · 稳定</strong></div>
            <p>种植、经营、Lucy 委托、好感成长和代际目标形成第一版完整循环。</p>
            <footer><span><GitCommitHorizontal :size="12" />基于 Design v2 · GameSpec v2</span><strong>9 / 9 PASS</strong></footer>
          </article>
        </div>
        <footer class="version-history-note"><Check :size="13" />Playable v1 已安全保留。本阶段不提供恢复操作。</footer>
      </aside>
    </div>
  </Transition>
</template>
