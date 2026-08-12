<script setup lang="ts">
import { Check, LoaderCircle } from 'lucide-vue-next'

defineProps<{ confirming: boolean }>()
</script>

<template>
  <section class="confirmation-state" role="status">
    <span class="confirmation-mark" :class="{ spinning: confirming }">
      <LoaderCircle v-if="confirming" :size="28" />
      <Check v-else :size="30" />
    </span>
    <span class="confirmation-kicker">{{ confirming ? 'FINALIZING DESIGN' : 'GAME DESIGN CONFIRMED' }}</span>
    <h3>{{ confirming ? '正在确认游戏设计…' : '游戏设计已确认' }}</h3>
    <p>我们正在把这个设计转换成<br />可以开发的游戏规格…</p>
    <div v-if="!confirming" class="next-placeholder">
      <span><Check :size="13" />Game Design</span>
      <i></i>
      <span>GameSpec · Coming next</span>
    </div>
  </section>
</template>
